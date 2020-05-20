#!/usr/bin/env python
# -*- coding:utf-8 -*-
from datetime import datetime
from sqlalchemy.orm.exc import NoResultFound
from flask import current_app as app
from aops.applications.database.models.repository.repository import FileReview
from aops.applications.exceptions.exception import NotFoundError, ResourcesNotFoundError, Error
from aops.applications.database.apis.repository.repository import Repostiory
from aops.applications.database.apis.system.message.message import create_message


def get_file_review_list(page, per_page, name=None, type=None, status=None, creator=None,
                         approver=None, fuzzy_query=None, business_group=None):
    """
    Get all file review items
    Returns:
        file review items list
    """
    q = FileReview.query.order_by(FileReview.updated_at.desc())

    if business_group:
        q = q.filter_by(business_group=business_group)

    # script name
    if name:
        q = q.filter(FileReview.scripts.name.like("%{}%".format(name)))

    if type:
        q = q.filter(FileReview.type.like("%{}%".format(type)))

    if status:
        if status == 'pending':
            q = q.filter(FileReview.status == 'pending' or FileReview.status == 'initial')
        else:
            q = q.filter(FileReview.status.like("%{}%".format(status)))

    if creator:
        q = q.filter(FileReview.submitter.like("%{}%".format(creator)))

    if approver:
        q = q.filter(FileReview.approver.like("%{}%".format(approver)))

    if fuzzy_query:
        q = q.filter(FileReview.name.concat(FileReview.name).
                     concat(FileReview.type).concat(FileReview.submitter).concat(FileReview.approver).
                     concat(FileReview.fuzzy_query).like("%{}%".format(fuzzy_query)))

    try:
        page = q.paginate(page=page, per_page=per_page)
        page.items = [item.update(risk_level=item.scripts[0].risk_level,
                                  comment=item.scripts[0].comment,
                                  project_id=item.scripts[0].project_id,
                                  path=item.scripts[0].full_path) for item in page.items if len(item.scripts) > 0]
        return page
    except Exception as e:
        app.logger.error("FileViews list failed: " + str(e))
        raise ResourcesNotFoundError("FileViews")


def get_file_review_with_id(identifier):
    """
    Get a file review with identifier
    Args:
        identifier: task review item ID

    Returns:
        Just the task review item with this ID
    """
    try:
        file_review = FileReview.query.filter_by(id=identifier, is_deleted=False).one()
    except NoResultFound:
        raise NotFoundError('FileReview', identifier)
    if len(file_review.scripts) == 0:
        raise Error(u'审批文件未包含文件信息', 410)
    return file_review.update(risk_level=file_review.scripts[0].risk_level, comment=file_review.scripts[0].comment,
                              project_id=file_review.scripts[0].project_id, path=file_review.scripts[0].full_path)


def _update_repository_item(identifier, **kwargs):
    script = Repostiory.get_repository_item_by_id(identifier)
    return script.update(**kwargs)


def review_file_with_id(identifier, review_info):
    """
    Review a file review with identifier
    Args:
        identifier:
        review_info: task review item ID

    Returns:
        Just the task review item with this ID
    """
    review_item = get_file_review_with_id(identifier)

    review_info.update(
        update_at=datetime.now(),
    )

    # merge request
    project_id = review_item.scripts[0].project_id
    merge_id = review_item.merge_id
    app.logger.debug("merge_id: {}".format(merge_id))
    if merge_id is None:
        raise Error(u'合并请求未创建', code=410)
    repository = Repostiory()
    if review_info.status == 'pass':
        repository.accept_merge_by_object(project_id, merge_id)
        if review_item.type == 'scripts':
            commit_sha = Repostiory().get_project_commit_list(project_id, {'type': 'last'})
            commit_sha = commit_sha.get('id')
            # generate script version items
            [Repostiory.create_script_version(script_id=script.file_id, commit_sha=commit_sha)
             for script in review_item.scripts]

        # update target_branch of repository_map table
        target_branch = review_item.target_branch
        target_branch = target_branch if target_branch else "master"
        [_update_repository_item(script.file_id, branch=target_branch,
                                 risk_level=review_info.risk_level,
                                 update_at=datetime.now()) for script in review_item.scripts]
    else:
        repository.delete_merge_by_object(project_id, merge_id)

    file_review = review_item.update(**review_info)

    # TODO: notice file's submitter and 引用此脚本的任务创建者
    # create_message(
    # message = Message(classify=args.classify,
    #                  risk_level=args.risk_level,
    #                  content=args.content,
    #                  status=args.statuss)
    # users = user_apis.get_users_with_names(args.usernames)
    # )
    return file_review.update(risk_level=file_review.scripts[0].risk_level, comment=file_review.scripts[0].comment)


def cancel_review_file_with_id(identifier):
    review_item = get_file_review_with_id(identifier=identifier)
    data = {
        'status': 'cancel'
    }
    merge_id = review_item.merge_id
    project_id = review_item.scripts[0].project_id
    Repostiory().delete_merge_by_object(project_id, merge_id)
    return review_item.update(**data)

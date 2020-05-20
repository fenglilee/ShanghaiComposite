#!/usr/bin/env python
# -*- coding:utf-8 -*-
from datetime import datetime


from flask import request, session
from sqlalchemy.orm.exc import NoResultFound
from aops.applications.database import db
from aops.applications.database.apis.system.message.message import create_message
from aops.applications.database.apis.task.task import get_task_with_id
from aops.applications.database.models.task.task import TaskReview, ReviewRecord
from aops.applications.exceptions.exception import ResourcesNotFoundError, ConflictError, \
    ResourceNotFoundError, ApproveYourselfError


def add_attribute(task_review):
    approve_record = ReviewRecord.query.filter_by(is_deleted=False, target_id=task_review.id).all()
    setattr(task_review, 'approve_record', approve_record)

def get_task_review_list(page, per_page, name=None, type=None, risk_level=None, status=None, creator=None, approver=None, fuzzy_query=None, start_time=None, end_time=None):
    """
    Get all task review items
    Returns:
        task review items list
    """
    business_group = request.cookies.get('BussinessGroup')

    q = TaskReview.query.filter_by(is_deleted=False, business_group=business_group).order_by(TaskReview.updated_at.desc())
    if name:
        q = q.filter(TaskReview.name.like(u"%{}%".format(name)))

    if type:
        q = q.filter(TaskReview.type.like(u"%{}%".format(type)))

    if risk_level:
        q = q.filter(TaskReview.risk_level.like(u"%{}%".format(risk_level)))

    if status:
        q = q.filter(TaskReview.status.like(u"%{}%".format(status)))

    if creator:
        q = q.filter(TaskReview.creator.like(u"%{}%".format(creator)))

    if approver:
        q = q.filter(TaskReview.approver.like(u"%{}%".format(approver)))

    if start_time and end_time:
        q = q.filter(TaskReview.created_at.between(start_time, end_time))

    if fuzzy_query:
        q = q.filter(TaskReview.name.concat(TaskReview.name).concat(TaskReview.type)
                     .concat(TaskReview.risk_level).concat(TaskReview.creator)
                     .concat(TaskReview.approver).concat(TaskReview.fuzzy_query)
                     .like(u"%{}%".format(fuzzy_query)))

    try:
        q = q.paginate(page=page, per_page=per_page)
        map(add_attribute, q.items)
        return q
    except Exception as e:
        raise ResourcesNotFoundError("TASKREVIEW")

def get_approver_list():
    """
    Get all task approver
    Returns:
        all task approver
    """
    q = ReviewRecord.query.filter_by(is_deleted=False).all()
    if q:
        return {'approver':set([approver.approver for approver in q])}
    return {}

def get_task_review_with_id(identifier):
    """
    Get a task review with identifier
    Args:
        identifier: task review item ID

    Returns:
        Just the task review item with this ID
    """
    try:
        task_review = TaskReview.query.filter_by(id=identifier, is_deleted=False).one()
    except NoResultFound:
        raise ResourceNotFoundError('TaskReview', identifier)

    approve_record = ReviewRecord.query.filter_by(is_deleted=False, target_id=task_review.id).all()
    if approve_record:
        setattr(task_review, 'approval_comments', approve_record[0].approval_comments)
        setattr(task_review, 'approve_record', approve_record)

    return task_review

def approval_task(identifier, args):
    """
    Approve a task that requires approval
    Args:
        identifier: task id
        args:  Approver's opinion

    Returns:
        Just the task review item with this ID
    """
    login_name = session.get('user_info').get('user')

    task_review = get_task_review_with_id(identifier)
    task = get_task_with_id(task_review.task_id)
    data = {
        'type': task_review.type,
        'language': task_review.language,
        'target_system': task_review.target_system,
        'description': task_review.description,
        'script_parameter': task_review.script_parameter,
        'time_out': task_review.time_out,
        'is_enable': task_review.is_enable,
        'creator': task_review.creator,
        'command': task_review.command,
        'risk_level': args.risk_level,
        'script': task_review.script,
        'risk_statement': args.risk_statement,
        'status': task_review.status,
        'file_selection': task_review.file_selection,
        'target_directory': task_review.target_directory,
        'file_owner': task_review.file_owner,
        'file_permission': task_review.file_permission,
        'is_replace': task_review.is_replace,
        'updated_at': datetime.now()
    }

    message_data = {
        'classify': 0,                                              # 0: notification, 1:confirmation
        'risk_level': args.risk_level,                              # 0:low, 1:middle, 2:high
        'content': 'Your task has been approved, please pay attention to view',
        'status': 0,                                                # 0: confirmed, 1:non-confirmed, 2:unconfirmed,
        'usernames': [task_review.creator]
    }

    def review(status):
        task_review.update(name=(task_review.name + u'-审批ID' + str(task_review.id)), approver=login_name,
                           status=status, risk_level=args.risk_level, risk_statement=args.risk_statement)
        setattr(task_review, 'approve_record', approve_record)
        return task_review

    if login_name == task_review.creator:
        raise ApproveYourselfError(ConflictError.message)

    approve_record = ReviewRecord.query.filter_by(target_id=task_review.id).first()
    if approve_record:
        raise ConflictError(ConflictError.message)

    ReviewRecord.create(is_deleted=False, status=args.status, approver=login_name, approval_comments=args.approval_comments,
                        updated_at=datetime.now(), risk_level=args.risk_level, target_id=identifier)
    # 审批修改内容
    if task.change_result:
        if args.status == 'pass':
            result = review(status=u'审批通过')
            data.update(change_result=u'修改内容，审批通过', status=u'审批通过', approver=login_name)
            task.update(**data)
            create_message(**message_data)
            return result
        else:
            result = review(status=u'审批不通过')
            task.change_result = u'修改内容,审批不通过'
            task.approver = login_name
            db.session.add(task)
            db.session.commit()
            create_message(**message_data)
            return result
    # 审批创建内容
    else:
        if args.status == 'pass':
            result = review(status=u'审批通过')
            task.status = u'审批通过'
            task.approver = login_name
            create_message(**message_data)
            db.session.add(task)
            db.session.commit()
            return result
        else:
            result = review(status=u'审批不通过')
            task.status = u'审批不通过'
            task.approver = login_name
            db.session.add(task)
            db.session.commit()
            create_message(**message_data)
            return result




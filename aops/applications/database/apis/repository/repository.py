#!/usr/bin/env python
# -*- coding:utf-8 -*-
from aops.applications.database.models.repository.repository import RepositoryModel, ScriptVersion, \
    FileReview
from flask import request, session, current_app as app
# from flask import session
import tempfile
import zipfile
import os
from datetime import datetime
import gitlab
from requests import exceptions as rexcept
from sqlalchemy import desc
from sqlalchemy.orm.exc import NoResultFound
from aops.applications.exceptions.exception import Error, ResourcesNotFoundError, ResourceNotFoundError, \
    ValidationError, ResourceAlreadyExistError, ResourceNotEmptyError, GitlabNotFoundError, GitlabError
from werkzeug.utils import secure_filename
from aops.applications.lib.gitlab_api import GitLabApi
from aops.applications.database.models import SysConfigBusiness
from aops.applications.database.models.task.task import Task
import re
from aops.applications.database.apis.system.sysconfig.approve_config import get_approve_configs

error_pattern = re.compile(
    """^Validation Error: \(mysql.connector.errors.IntegrityError\) 1062 \(23000\): Duplicate entry (?P<content>.*?) for key (?P<key>.*?) (.*)'"""
)


class Repostiory(object):
    def __init__(self, gitlab_url=None, private_token=None, user=None, email=None):
        if gitlab_url is None:
            gitlab_url = app.config.get('GITLAB_URL')
        if private_token is None:
            private_token = app.config.get('GITLAB_TOKEN')
        self.gl = gitlab.Gitlab(gitlab_url, private_token=private_token, timeout=10)
        if user is None:
            user_info = session.get('user_info', {'user': 'admin'})
            self.user = user_info.get('user')
        else:
            self.user = user
        self.email = email if email is not None else app.config.get('GITLAB_EMAIL', 'system@aops.com')

    def gitlab_init(self, group_name):
        group = self.create_gitlab_group(name=group_name, path=group_name)
        app.logger.info("gitlab init add group: {}".format(group.attributes))

        s = self.create_gitlab_group(name='scripts', path='scripts', parent_id=group.id)
        app.logger.info("gitlab init add group: {}".format(s.attributes))
        self.create_gitlab_group(name='linux', path='linux', parent_id=s.id)
        self.create_gitlab_group(name='windows', path='windows', parent_id=s.id)

        c = self.create_gitlab_group(name='configurations', path='configurations', parent_id=group.id)
        app.logger.info("gitlab init add group: {}".format(c.attributes))

        a = self.create_gitlab_group(name='applications', path='applications', parent_id=group.id)
        app.logger.info("gitlab init add group: {}".format(a.attributes))

        f = self.create_gitlab_group(name='file_buckets', path='file_buckets', parent_id=group.id)
        app.logger.info("gitlab init add group: {}".format(f.attributes))
        home = self.create_project(project_name='home', group_id=f.id)
        app.logger.info("gitlab init add file_buckets home project: {}".format(home))

        data = [
            {'name': group_name, 'absolute_path': group_name, 'type': 'tree', 'update_user': self.user},
            {'path': group_name, 'name': 'scripts', 'absolute_path': os.path.join(group_name, 'scripts'),
             'type': 'tree', 'update_user': self.user},
            {'path': group_name, 'name': 'applications', 'absolute_path': os.path.join(group_name, 'applications'),
             'type': 'tree', 'update_user': self.user},
            {'path': group_name, 'name': 'configurations', 'absolute_path': os.path.join(group_name, 'configurations'),
             'type': 'tree', 'update_user': self.user},
            {'path': group_name, 'name': 'file_buckets', 'absolute_path': os.path.join(group_name, 'file_buckets'),
             'type': 'tree', 'update_user': self.user},
            {'path': os.path.join(group_name, 'scripts'), 'name': 'linux',
             'absolute_path': os.path.join(group_name, 'scripts/linux'), 'type': 'tree', 'update_user': self.user},
            {'path': os.path.join(group_name, 'scripts'), 'name': 'windows',
             'absolute_path': os.path.join(group_name, 'scripts/windows'), 'type': 'tree', 'update_user': self.user},
        ]
        [RepositoryModel.create(**item) for item in data]

    def create_gitlab_group(self, name, path, parent_id=None):
        try:
            group = self.gl.groups.create({'name': name, 'path': path, 'parent_id': parent_id})
        except gitlab.GitlabCreateError as e:
            raise Error(e.error_message, e.response_code)
        return group

    @classmethod
    def get_repository_item_by_id(cls, identifier):
        try:
            item = RepositoryModel.query.filter_by(file_id=identifier).one()
        except NoResultFound:
            raise ResourceNotFoundError('RepositoryItem', id)
        return item

    @classmethod
    def _get_repository_item(cls, project_id, full_path):
        try:
            item = RepositoryModel.query.filter_by(project_id=project_id, full_path=full_path).one()
        except NoResultFound:
            raise ResourceNotFoundError('RepositoryItem', full_path)
        return item

    @classmethod
    def _create_file_view(cls, **kwargs):
        try:
            todo = FileReview.create(**kwargs)
        except ValidationError as e:
            raise Error(e.message, code=409)
        return todo

    @classmethod
    def generate_tmp_branch(cls):
        """
        Returns: tmp branch name

        """
        d = datetime.now()
        return "patch-" + d.strftime("%y%m%d_%H%M%S")

    @staticmethod
    def _generate_script_version():
        d = datetime.now()
        return d.strftime("%y%m%d_%H%M%S")

    @staticmethod
    def _get_file_items(project_id, path, branch):
        try:
            items = RepositoryModel.query.filter_by(path=path, project_id=project_id, branch=branch).all()
        except NoResultFound as e:
            raise Error(" path {} branch {} can not be found".format(path, branch), code=404)
        return items

    def _get_project_object(self, project_id):
        try:
            project = self.gl.projects.get(project_id)
        except gitlab.exceptions.GitlabGetError:
            raise GitlabNotFoundError('Gitlab Project', project_id)
        return project

    def _get_file_object(self, project_id, file_path, ref):
        p = self._get_project_object(project_id)
        try:
            f = p.files.get(file_path=file_path, ref=ref)
        except gitlab.GitlabGetError:
            raise GitlabNotFoundError('Gitlab File', file_path)
        return f

    @classmethod
    def _delete_file_object(cls, file_obj, commit_message, branch):
        try:
            deleted = file_obj.delete(commit_message=commit_message, branch=branch)
        except gitlab.GitlabDeleteError as e:
            raise GitlabError(e.error_message, e.response_code)
        return deleted

    @classmethod
    def _create_repository_item(cls, **kwargs):
        try:
            item = RepositoryModel.create(**kwargs)
        except ValidationError as e:
            re_res = re.search(error_pattern, e.msg)
            raise ValidationError('{} {} has already existed'.format(re_res.group('key'), re_res.group('content')))
        return item

    def get_project_by_id(self, project_id):
        p = self._get_project_object(project_id)
        return p

    def get_repository_list(self):
        """
        Based on repository_type get group and project info.
        Args:
            *args:

        Returns:

        """
        business_groups = SysConfigBusiness.query.filter_by(is_deleted=False).all()
        business_group_list = [group.name for group in business_groups]
        try:
            groups_list = self.gl.groups.list(all=True)
        except rexcept.ConnectTimeout as e:
            raise Error(msg=e.message, code=504)
        groups = []
        for business_name in business_group_list:
            app.logger.debug("business name: {}".format(business_name))
            group = [group for group in groups_list if group.name == business_name and
                     group.attributes.get('parent_id') is None]
            if len(group) == 1:
                business_group_id = group[0].id
                business_group_name = group[0].name
                business_group_desc = group[0].description
                groups.append({"id": business_group_id, "name": business_group_name, "description": business_group_desc})
        return groups

    def get_sub_repository_list(self, group_name, repository_type):
        """
        Based on repository_type get group and project info.
        Args:
            group_name:
            repository_type: scripts/applications/configurations/file_buckets

        Returns:

        """
        groups_list = self.gl.groups.list(all=True)
        group = [group for group in groups_list if group.name == group_name and
                 group.attributes.get('parent_id') is None]
        business_group_id = group[0].id

        app.logger.debug("group: {}".format(group[0].name))

        sub_group = [sub for sub in groups_list if sub.attributes.get('parent_id') ==
                     business_group_id and sub.name == repository_type]

        app.logger.debug("sub group: {}".format(sub_group))
        if len(sub_group) == 0:
            return []

        if repository_type == "scripts":
            # repository_type [scripts]
            sub_group_id = sub_group[0].id
            # linux/windows
            sub_system = [sub.attributes for
                          sub in groups_list if sub.attributes.get('parent_id') == sub_group_id]
        else:
            sub_system = [sub.attributes for sub in sub_group]
        return sub_system

    def get_project_list(self, args, business_group):
        """
        Based on repository_type get group and project info.
        Args:
            *args:
            business_group:
        Returns:

        """
        try:
            group = self.gl.groups.get(args.group_id)
        except gitlab.GitlabGetError:
            raise ResourceNotFoundError("Gitlab Group", args.group_id)

        if group.name in ['linux', 'windows']:
            path = os.path.join(business_group, 'scripts', group.name)
        else:
            path = os.path.join(business_group, group.name)
        q = RepositoryModel.query.filter_by(business_group=business_group, path=path)
        return [item for item in q.all() if item.full_path == item.project_name]

    def get_project_file_by_path(self, project_id, args):
        """
        Args:
            project_id:
            args:

        Returns:

        """
        path = args.path if args.get('path') else '/'
        branch = args.branch if args.get('branch') else 'master'
        if len(branch) == 40:
            # commits file list
            items = self.get_project_files_by_commit(project_id, branch, path)
        else:
            # branch file list
            items = RepositoryModel.query.filter_by(project_id=project_id, path=path, branch=branch).all()
        return items

    def get_project_commit_list(self, project_id, args):
        project = self._get_project_object(project_id)
        commits_list = [commit.attributes for commit in project.commits.list()]
        commit_type = args.get('type')
        commit_type = "all" if commit_type is None else commit_type
        app.logger.debug("commit_type parms: {}".format(commit_type))
        if commit_type == 'last':
            if len(commits_list) > 0:
                return commits_list[0]
            else:
                Error(u'项目未存在任何提交记录', 404)
        else:
            return commits_list

    def get_project_files_by_commit(self, project_id, commit_sha, path):
        p = self._get_project_object(project_id)
        glapi = GitLabApi(app.config.get('GITLAB_URL'), app.config.get('GITLAB_TOKEN'))
        path = path if path else None
        try:
            items = p.repository_tree(ref=commit_sha, path=path)
        except gitlab.exceptions.GitlabGetError:
            ResourceNotFoundError('Gitlab branch:', commit_sha)
        for item in items:
            commit = glapi.get_last_commit_by_path(project_id, item.get('path'), ref_name=commit_sha)
            item.update(comment=commit.get('title'))
            item.update(updated_at=commit.get('committed_date'))
            item.update(project_id=project_id)
            item.update(full_path=item.get('path'))
        return items

    def get_file_diffs_by_commit(self, project_id, commit_sha, branch):
        """

        Args:
            project_id:
            commit_sha:
            branch:

        Returns:

        """
        project = self._get_project_object(project_id)
        commit = project.commits.get(commit_sha)
        diffs = commit.diff()
        [commit.update(new_content=self.get_file_content_by_commit(project_id, commit.get('new_path'), commit_sha,
                                                                   commit)) for commit in diffs]
        [commit.update(old_content=self.get_file_content_by_commit(project_id, commit.get('old_path'), branch,
                                                                   commit)) for commit in diffs]
        return diffs

    def get_file_content_by_commit(self, project_id, full_path, commit_sha, commit):
        p = self._get_project_object(project_id)
        try:
            f = p.files.get(file_path=full_path, ref=commit_sha)
        except gitlab.exceptions.GitlabGetError:
            app.logger.info("get_file_content_by_commit: commit_sha:{}, {} not found, ".format(commit_sha, full_path))
            return ""
        if commit.get('diff').split()[0] == 'Binary':
            return "Binary files"
        return f.decode()

    @classmethod
    def _get_item(cls, **kwargs):
        try:
            item = RepositoryModel.query.filter_by(**kwargs).one()
        except NoResultFound:
            raise Error("Repository item can not be found. args: {}".format(kwargs))
        return item

    @classmethod
    def get_file_distributions_list(cls, args):
        path = args.path
        branch = args.branch if args.branch else 'master'
        data = {
            'absolute_path': path
        }
        item = cls._get_item(**data)
        app.logger.debug('item: {}'.format(item))
        if item.project_id:
            project_id = item.project_id
            full_path = item.full_path
            if not item.path.startswith('/') and item.project_name == full_path:
                path = '/'
            else:
                path = os.path.join('/', full_path)
            return RepositoryModel.query.filter_by(path=path, branch=branch, project_id=project_id).all()
        else:
            return RepositoryModel.query.filter_by(path=path).all()

    def get_project_branches_list(self, project_id):
        """
        Args:
            project_id: project id

        Returns: branches list

        """
        project = self._get_project_object(project_id)
        return [branch.attributes for branch in project.branches.list() if not branch.name.startswith('patch-')]

    def create_project_branch(self, project_id, args):
        """
        Args:
            project_id:
            args:

        Returns: branch attributes

        """
        project = self._get_project_object(project_id)
        ref = args.get('copy_from')
        ref = "master" if ref is None else ref
        try:
            branch = project.branches.create({'branch': args.name, 'ref': ref})
        except gitlab.exceptions.GitlabCreateError as e:
            raise Error(msg=e.error_message, code=e.response_code)
        return branch.attributes

    def delete_project_branch(self, project_id, args):
        project = self._get_project_object(project_id)
        try:
            branch = project.branches.get(args.name)
            branch.delete()
        except gitlab.exceptions.GitlabDeleteError as e:
            raise Error(msg=e.error_message, code=e.response_code)
        return branch.attributes

    def create_project(self, project_name, group_id):
        """
        Args:
            args：project_name, group_id

        Returns: project_id, project_name

        """

        try:
            project = self.gl.projects.create({'name': project_name, 'namespace_id': group_id})
        except gitlab.GitlabCreateError as e:
            raise Error(e.error_message, e.response_code)
        path = project.namespace.get('full_path')
        absolute_path = os.path.join(path, project.name)
        business_group = request.cookies.get('BussinessGroup', 'LDDS')
        data = {
            'path': path,
            'name': project.name,
            'full_path': project.name,
            'absolute_path': absolute_path,
            'type': 'tree',
            'update_user': self.user,
            'project_id': project.id,
            'project_name': project.name,
            'business_group': business_group
        }
        try:
            RepositoryModel.create(**data)
        except ValidationError:
            raise ResourceAlreadyExistError("project item")
        return {"id": project.id, "name": project.name}

    def delete_project(self, project_id):
        """

        Args:
            project_id
        Returns:

        """
        project = self._get_project_object(project_id)
        path = project.namespace.get('full_path')
        try:
            project.delete()
        except gitlab.GitlabDeleteError as e:
            raise GitlabError(e.message, e.response_code)
        try:
            project_item = RepositoryModel.query.filter_by(name=project.name, path=path).one()
            project_item.delete()
        except NoResultFound as e:
            app.logger.info("Did not find: {}, failed".format(e.message))
        return {"id": project.id, "name": project.name}

    def create_project_file(self, project_id, args):
        """

        Args:
            project_id:
            args:

        Returns:

        """
        business_group = args.business_group if args.business_group else 'LDDS'
        project = self._get_project_object(project_id)
        path = args.path
        file_path = os.path.join(path, args.name.encode('utf-8'))
        full_path = file_path[1:] if file_path.startswith('/') else file_path

        project_full_path = os.path.join(project.namespace.get('full_path'), project.name)
        absolute_path = os.path.join(project_full_path, full_path)

        if args.get('branch', None):
            branch = args.branch
        else:
            branch = "master"

        item_type = 'blob' if args.get('type') is None else args.get('type')
        try:
            if item_type == "tree":
                project.files.create({'file_path': os.path.join(file_path, ".gitkeep"), 'branch': branch,
                                      'content': "Create by system", 'author_email': self.email,
                                      'author_name': self.user, 'commit_message': 'create dir {}'.format(file_path)
                                      })
            else:
                project.files.create({'file_path': file_path, 'branch': branch, 'content': "Create by system",
                                      'author_email': self.email,
                                      'author_name': self.user,
                                      'commit_message': 'create {}'.format(file_path)})
        except gitlab.exceptions.GitlabCreateError as e:
            raise Error(msg=e.error_message, code=e.response_code)
        # update script_repository map table
        # TODO: based on file_full_path generate file's parent directory.
        # file_name = file_path.split('/')[-1]
        # if file_path.startswith('/'):
        #    file_items = file_path.split('/')
        #    length = len(file_items)

        data = {
            'name': args.name,
            'path': path,
            'full_path': full_path,
            'absolute_path': absolute_path,
            'risk_level': 1,
            'project_id': project_id,
            'project_name': project.name,
            'update_user': self.user,
            'type': item_type,
            'comment': 'Create {}'.format(file_path),
            'branch': branch,
            'business_group': business_group
        }
        create_item = self._create_repository_item(**data)
        return create_item.to_dict()

    def get_project_file_content(self, project_id, args):
        """
        从gitlab获取文件内容
        file_path, branch_name="master"
        Args:
            project_id:
            args:
        Returns:

        """
        project = self.gl.projects.get(id=project_id)
        branch = args.get('branch')
        branch = "master" if branch is None else branch
        app.logger.debug("params: branch {}".format(branch))
        # get the base64 encoded content
        # return project.files.get(file_path=file_path, ref=branch_name).content

        # get the decoded content
        # return project.files.get(file_path=args.file_path, ref=args.branch).decode()
        file_item = RepositoryModel.query.filter_by(full_path=args.full_path, project_id=project_id).first()
        app.logger.debug(file_item)
        file_dict = file_item.to_dict() if file_item else {}
        try:
            f = project.files.get(file_path=args.full_path, ref=branch)
        except gitlab.GitlabGetError as e:
            raise Error(e.error_message, code=e.response_code)
        # file_dict.update({"content": unicode(f.decode(), 'utf-8')})
        file_dict.update(content=f.decode())
        file_dict.update(size=f.size)
        # when the data get from gitlab, append file_name
        file_dict.update(name=f.file_name)

        return file_dict

    @staticmethod
    def get_review_status(repository_type):
        approve_config = get_approve_configs()

        if repository_type == 'scripts':
            if approve_config.script_on:
                review = True
            else:
                review = False
        elif repository_type == 'applications':
            if approve_config.software_on:
                review = True
            else:
                review = False
        elif repository_type == 'configurations':
            if approve_config.config_on:
                review = True
            else:
                review = False
        else:
            review = False
        return review

    def update_project_file_content(self, project_id, args):
        """
        首先从gitlab获取文件内容，编辑后将文件存储至service-backend workspace.
        Returns:

        """
        project = self.gl.projects.get(project_id)
        branch = "master" if args.get('branch') is None else args.get('branch')
        repository_type = args.get('repository_type')
        business_group = args.get('business_group')
        file_content = args.content.encode('utf-8')

        review = self.get_review_status(repository_type)
        app.logger.debug("review: {}".format(review))
        file_item = self._get_repository_item(project_id=project_id, full_path=args.full_path)
        try:
            f = project.files.get(file_path=args.full_path, ref=branch)
        except gitlab.exceptions.GitlabGetError:
            ResourceNotFoundError("Gtilab project file", args.full_path)

        if review:
            tmp_branch = self.generate_tmp_branch()
            created_branch = project.branches.create({'branch': tmp_branch, 'ref': branch})
            app.logger.info("created_branch: {}".format(created_branch.name))

            file_item.update(comment=args.comment)

            f.content = file_content
            f.save(branch=tmp_branch, commit_message='Update file: {}'.format(args.full_path))

            mr = self.create_merge_request_by_project_id(project_id, source_branch=tmp_branch,
                                                         target_branch=branch,
                                                         title='aops system merge request, branch: ' + tmp_branch
                                                         )
            commit_sha = [commit.id for commit in mr.commits()][0]
            app.logger.debug("project_id: {}, mr_id: {}".format(project_id, mr.id))
            review_item = self._create_file_view(submitter=self.user, status='pending', type=repository_type,
                                                 target_branch=branch, merge_id=mr.get_id(), commit_sha=commit_sha,
                                                 business_group=business_group)
            review_item.scripts.append(file_item)
            review_item.save()

            review_id = review_item.id
            app.logger.debug("review_id: " + str(review_id))

            return file_item
        else:
            f.content = file_content
            f.save(branch=branch, commit_message='Update file: {}'.format(args.full_path))
            file_info = {"comment": args.comment, "risk_level": args.risk_level, "update_user": self.user}
            return file_item.update(**file_info) if file_item else {}

    @staticmethod
    def validate_extension(f):
        return '.' in f and f.split('.')[-1] not in app.config['UPLOADED_FILES_DENY']

    @classmethod
    def upload_project_file(cls, project_id, args):
        """
        文件存储至server-backend
        Returns:

        """
        f = args.file
        file_name = secure_filename(f.filename)
        success = False
        if not file_name:
            return {'IsSuccess': success, "message": u"文件名禁止使用中文"}
        if f and cls.validate_extension(file_name):
            upload_script_dir = os.path.join(app.config.get('UPLOAD_FOLDER'), str(project_id))
            try:
                if not os.path.exists(upload_script_dir):
                    os.mkdir(upload_script_dir)
            except OSError as e:
                raise Error(msg=e, code=403)
            upload_tmp_dir = tempfile.mkdtemp(dir=upload_script_dir)
            upload_tmp_file = os.path.join(upload_tmp_dir, file_name)
            f.save(upload_tmp_file)

            if args.unzip:
                file_name = file_name[:-4]
                f = zipfile.ZipFile(upload_tmp_file)
                f.extractall(path=upload_tmp_dir)
                os.remove(upload_tmp_file)
            success = True
            return {'IsSuccess': success, "name": file_name, "server_path": upload_tmp_dir}
        else:
            return {'IsSuccess': success, "message": u"请检查文件扩展名或是超出上传文件限制(500M)"}

    def upload_files_submit(self, project_id, args):
        """
        Args:
            project_id:
            args: upload file and upload zip package.
        Returns:

        """
        files = args.files
        comment = args.comment
        risk_level = args.risk_level
        path = args.path
        branch = args.branch
        repository_type = args.repository_type
        business_group = args.business_group if args.business_group else 'LDDS'
        # unzip = args.unzip
        target_branch = branch if branch else "master"

        review = self.get_review_status(repository_type)

        tmp_branch = target_branch if review is False else self.generate_tmp_branch()
        project = self._get_project_object(project_id)
        project_full_path = os.path.join(project.namespace.get('full_path'), project.name)

        created_list = []
        for f in files:
            name = f.get('name')
            file_path = os.path.join(path, name)
            full_path = file_path[1:] if file_path.startswith('/') else file_path
            absolute_path = os.path.join(project_full_path, full_path)
            data = {
                'name': name,
                'path': path,
                'full_path': full_path,
                'absolute_path': absolute_path,
                'risk_level': risk_level,
                'project_id': project_id,
                'project_name': project.name,
                'update_user': self.user,
                'type': 'blob',
                'comment': comment,
                'branch': tmp_branch,
                'business_group': business_group
            }

            create_item = self._create_repository_item(**data)
            created_list.append(create_item)

        if review:
            review_item = self._create_file_view(submitter=self.user, status='initial', type=repository_type,
                                                 target_branch=target_branch, scripts=created_list,
                                                 business_group=business_group)

            app.logger.debug("review_id: {}".format(review_item.id))
            review_id = review_item.id
        else:
            review_id = None

        user_info = session.get('user_info', {'user': 'admin'})
        creator = user_info.get('user')
        gs = gevent.spawn(file_controller, app._get_current_object(), project_id=project_id, path=path, files=files,
                          comment=comment, review_id=review_id, target_branch=target_branch, creator=creator)
        gs.start()

        return created_list

    @classmethod
    def return_chunk(cls, chunk):
        print("chunk:" + chunk)
        yield chunk

    def download_project_archive(self, project_id, chunk_size):
        project = self.gl.projects.get(project_id)
        return project.repository_archive(streamed=True, chunk_size=chunk_size, action=self.return_chunk)

    def download_project_file(self, project_id, args):
        try:
            file_item = RepositoryModel.query.filter_by(project_id=project_id, file_id=args.id).one()
        except NoResultFound:
            raise ResourceNotFoundError("file item", args.id)

        f = self._get_file_object(project_id, file_path=file_item.full_path, ref=file_item.branch)
        return f.decode(), f.file_name

    @classmethod
    def get_project_files(cls, project_id, args):
        try:
            script_file = RepositoryModel.query.filter(RepositoryModel.file_id.in_(args.ids)).\
                filter_by(project_id=project_id).all()
        except NoResultFound:
            raise ResourcesNotFoundError('project_{}\'s_file'.format(project_id))
        return script_file

    @staticmethod
    def _check_task_in_used(file_path, project_id):
        is_used = Task.query.filter_by(script=file_path, project_id=project_id).all()
        if is_used:
            app.logger.info("file: {} was used by task: {}.".format(file_path, is_used.task_name))
            raise Error(u'file was used by task: {}'.format(is_used.task_name), code=409)

    def delete_project_file(self, project_id, args):
        """
        Args:
            project_id:
            args:

        Returns:
            the object of deleted files/dirs
        Raises:
            ResourceNotEmptyError
        """
        script_file = RepositoryModel.query.filter(RepositoryModel.file_id.in_(args.ids)). \
            filter_by(project_id=project_id).all()

        branch = args.get('branch')
        branch_name = "master" if branch is None else branch

        for file_item in script_file:
            if file_item.type == 'tree':
                path = file_item.full_path
                dir_items = self._get_file_items(project_id, path, branch_name)
                if dir_items:
                    raise ResourceNotEmptyError(dir_items)
                else:
                    file_item.delete()
                file_path = file_item.full_path + '/.gitkeep'
            else:
                file_item.delete()
                file_path = file_item.full_path
                self._check_task_in_used(file_path, project_id)
            f = self._get_file_object(project_id, file_path, ref=branch_name)
            self._delete_file_object(f, commit_message="Delete {} by {}".format(file_path, self.user),
                                     branch=branch_name)
        app.logger.debug("script_file: {}".format(script_file))
        return True

    @staticmethod
    def _check_group_list_length(group_list, group=None):
        if len(group_list) == 0:
            raise GitlabNotFoundError("Gitlab group", u'{}'.format(group))

    def get_script_system_language_map(self, business_group):
        try:
            groups_list = self.gl.groups.list(all=True)
            business_group_id = [group.id for group in groups_list if group.name == business_group and
                                 group.parent_id is None]
            self._check_group_list_length(business_group_id, business_group)
            app.logger.debug("sub_group: {}".format(business_group_id))
            sub = [sub for sub in groups_list if sub.name == 'scripts' and sub.parent_id == business_group_id[0]]
            self._check_group_list_length(sub, "scripts")
            linux_group_info = [group.projects.list() for group in groups_list if group.name == 'linux' and
                                group.parent_id == sub[0].id]
            self._check_group_list_length(sub, "linux")
            windows_group_info = [group.projects.list() for group in groups_list if group.name == 'windows' and
                                group.parent_id == sub[0].id]
            self._check_group_list_length(sub, "windows")
            app.logger.debug("windows_group_info: {}".format(windows_group_info[0]))
        except gitlab.GitlabGetError as e:
            raise Error(e.message, e.response_code)
        windows_project = [{"name": project.name, "id": project.id} for project in windows_group_info[0] if windows_group_info[0]]
        linux_language = [{"name": project.name, "id": project.id} for project in linux_group_info[0] if linux_group_info[0]]
        return {"linux": linux_language, "windows": windows_project}

    @classmethod
    def get_script_list(cls, args):
        scripts = RepositoryModel.query.filter_by(project_id=args.id, is_deleted=False, type='blob').\
            order_by(desc(RepositoryModel.updated_at))
        # Fuzzy query example
        fuzzy_query = args.fuzzy_query
        if args.fuzzy_query:
            scripts = scripts.filter(RepositoryModel.name.concat(RepositoryModel.comment).
                                     concat(RepositoryModel.full_path).like("%{}%".format(fuzzy_query)))

        # return pagination body
        try:
            return [script.to_dict() for script in scripts.all()]
        except Exception:
            raise ResourcesNotFoundError("Scripts")

    @classmethod
    def get_script_version_list(cls, script_id):
        try:
            scripts_version = ScriptVersion.query.filter_by(script_id=script_id).all()
        except NoResultFound:
            raise ResourceNotFoundError("script_version", script_id)
        return scripts_version

    def create_merge_request_by_project_id(self, project_id, source_branch, target_branch, title):
        project = self._get_project_object(project_id)
        try:
            mr = project.mergerequests.create({'source_branch': source_branch, 'target_branch': target_branch,
                                               'title': title
                                               })
        except gitlab.exceptions.GitlabCreateError as e:
            raise Error(e.error_message, e.response_code)
        return mr

    def get_merge_by_id(self, project_id, merge_id):
        project = self._get_project_object(project_id)
        try:
            mr = project.mergerequests.get(merge_id)
        except gitlab.exceptions.GitlabGetError:
            raise ResourceNotFoundError('Gitlab merge request', merge_id)
        return mr

    def accept_merge_by_object(self, project_id, merge_id):
        mr = self.get_merge_by_id(project_id, merge_id)
        try:
            mr.merge(should_remove_source_branch=False)
        except gitlab.exceptions.GitlabMRClosedError as e:
            if e.response_code == 405:
                raise Error(u'不能重复审批', 405)
            else:
                raise Error(e.error_message, e.response_code)
        except gitlab.exceptions.GitlabAuthenticationError as e:
            raise Error(e.error_message, e.response_code)

    def delete_merge_by_object(self, project_id, merge_id):
        mr = self.get_merge_by_id(project_id, merge_id)
        try:
            mr.delete()
        except gitlab.exceptions.GitlabMRClosedError as e:
            raise Error(e.error_message, e.response_code)
        except gitlab.exceptions.GitlabAuthenticationError as e:
            raise Error(e.error_message, e.response_code)

    @classmethod
    def create_script_version(cls, script_id, commit_sha):
        version = cls._generate_script_version()
        repository = RepositoryModel.query.filter_by(file_id=script_id).one()
        sv = ScriptVersion.create(commit_sha=commit_sha, version=version, script_id=repository.file_id)
        return sv

    @staticmethod
    def _check_group_length(group=None):
        if len(group) == 0:
            raise GitlabError('Gitlab group : {} can not be found'.format(group), code=400)

    def count_repository_projects(self, business_group=None, start_time=None, end_time=None):
        groups_list = self.gl.groups.list(all=True)
        if business_group:
            group = [group.id for group in groups_list if group.parent_id is None and
                 group.name == business_group]
            self._check_group_length(group)
            group_id = group[0]

            scripts = [group for group in groups_list if group.parent_id == group_id and group.name == 'scripts']
            self._check_group_length(scripts)
            scripts_id = scripts[0].id

            scripts_sub = [group for group in groups_list if group.parent_id == scripts_id]
            self._check_group_length(scripts_sub)
            scripts_count = 0
            for sub in scripts_sub:
                count = len(sub.projects.list())
                scripts_count += count

            applications = [group for group in groups_list if group.parent_id == group_id and
                            group.name == 'applications']
            self._check_group_length(applications)
            application_group = self.gl.groups.get(applications[0].id)
            applications_count = len(application_group.projects.list())

            configurations = [group for group in groups_list if group.parent_id == group_id and
                            group.name == 'configurations']
            self._check_group_length(configurations)
            configurations_group = self.gl.groups.get(configurations[0].id)
            configurations_count = len(configurations_group.projects.list())

            return dict(scripts_count=scripts_count,applications_count=applications_count,
                        configurations_count=configurations_count)
        else:
            raise Error(u'未获取到BusinessGroup', code=400)


import gevent
from .gitfile import file_controller
# from gevent import exceptions

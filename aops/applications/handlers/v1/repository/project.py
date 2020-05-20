#!/usr/bin/env python
# -*- coding:utf-8 -*-
from flask_restplus import Resource, fields, Model, reqparse
from flask import abort, request, Response, current_app as app
from aops.applications.handlers.v1.repository import ns
from aops.applications.handlers.v1.repository.repository import repository_fields, repository_model, \
    script_model, script_repository_model
from aops.applications.database.apis.repository.repository import Repostiory
from aops.applications.exceptions.exception import Error, ResourceNotFoundError, ResourceNotEmptyError, \
    GitlabNotFoundError, GitlabError, ResourcesNotFoundError, ValidationError
from werkzeug.datastructures import FileStorage
from aops.applications.handlers.v1 import passport_auth


commit_diff_model = Model('CommitDiff', {
    'new_path': fields.String(),
    'new_file': fields.Boolean(),
    'new_content': fields.String(),
    'renamed_file': fields.Boolean(),
    'deleted_file': fields.Boolean,
    'old_path': fields.String,
    'old_content': fields.String()

})
project_commit_model = Model('ProjectCommit', {
    'committer_email': fields.String(),
    'title': fields.String,
    'committer_name': fields.String,
    'committed_date': fields.String,
    'id': fields.String
})

project_branch_model = Model('ProjectBranch', {
    'name': fields.String(required=True),
})

project_branch_return = Model.clone("BranchResponse", project_branch_model, {
    'project_id': fields.Integer
})

project_create_branch = Model.clone("CreateBranch", project_branch_model, {
    'copy_from': fields.String(description='copy from which version, default use: master')
})

project_create_file = Model('create_file_fields', {
    'name': fields.String(),
    'path': fields.String,
    'type': fields.String(default='blob', description='item\' type file/directory'),
    'branch': fields.String
})

project_update_file = Model('UpdateFile', {
    'full_path': fields.String,
    'branch': fields.String,
    'risk_level': fields.Integer(default=0, description='risk level'),
    'content': fields.String,
    'comment': fields.String,
    'repository_type': fields.String
})

upload_file_item = Model('FileItem', {
    'name': fields.String,
    'server_path': fields.String
})
project_upload_file = Model('UploadFile', {
    'files': fields.List(fields.Nested(upload_file_item)),
    'path': fields.String,
    'branch': fields.String,
    'risk_level': fields.Integer(default=0, description='risk level'),
    'comment': fields.String,
    'repository_type': fields.String(require=True, descrption='project type, scripts/applications/configurations')
})

project_delete_file = Model('DeleteFile', {
    'ids': fields.List(fields.Integer)
})

project_upload_return = Model('FileUpload', {
    'IsSuccess': fields.Boolean(),
    'name': fields.String(descrption="file's name"),
    'server_path': fields.String(),
    'message': fields.String()
})

project_download_return = Model('FileDownload', {
    'IsSuccess': fields.Boolean(),
    'name': fields.String(descrption="file's name"),
    'server_path': fields.String()
})

project_file_model = Model('File', {
    'id': fields.String(),
    'path': fields.String(required=True, description='The file path based on project /'),
    'type': fields.String(required=True, default=False, description='whether is directory or not'),
    'name': fields.String(),
    'comment': fields.String(),
    'project_id': fields.Integer,
    'updated_at': fields.String()
})

ns.add_model(project_file_model.name, project_file_model)
ns.add_model(project_create_file.name, project_create_file)
ns.add_model(project_delete_file.name, project_delete_file)
ns.add_model(project_update_file.name, project_update_file)
ns.add_model(project_upload_return.name, project_upload_return)
ns.add_model(project_download_return.name, project_download_return)
ns.add_model(project_upload_file.name, project_upload_file)
ns.add_model(upload_file_item.name, upload_file_item)
ns.add_model(commit_diff_model.name, commit_diff_model)
ns.add_model(project_commit_model.name, project_commit_model)
ns.add_model(project_branch_model.name, project_branch_model)
ns.add_model(project_create_branch.name, project_create_branch)
ns.add_model(project_branch_return.name, project_branch_return)


script_project_parser = reqparse.RequestParser()
script_project_parser.add_argument('path', type=str, help="default path is /")
script_project_parser.add_argument('branch', type=str, help="default branch is master")

script_file_parser = reqparse.RequestParser()
script_file_parser.add_argument('full_path', type=str, required=True),
script_file_parser.add_argument('branch', type=str)

project_file_update_args = script_file_parser.copy()
project_file_update_args.add_argument('content', required=True)
project_file_update_args.add_argument('comment', required=True)
project_file_update_args.add_argument('risk_level', type=int, required=False)
project_file_update_args.add_argument('repository_type', type=str, required=True,
                                help="project type, scripts/applications/configurations")

project_commit_parser = reqparse.RequestParser()
project_commit_parser.add_argument('type', type=str, help="full commit list or last commit: [last|all] ")

project_files_by_commit_args = reqparse.RequestParser()
project_files_by_commit_args.add_argument('path', type=str, help="repository tree base on path")

project_file_without_name = reqparse.RequestParser()
project_file_without_name.add_argument('path', type=str, required=True)
project_file_without_name.add_argument('type', type=str)
project_file_without_name.add_argument('branch', type=str)

project_file_parser = project_file_without_name.copy()
project_file_parser.add_argument('name', required=True)
project_file_parser.add_argument('business_group', location='args')

project_delete_file_parser = reqparse.RequestParser()
project_delete_file_parser.add_argument('ids', type=list, required=True, location='json')

project_upload_parser = reqparse.RequestParser()
project_upload_parser.add_argument('file', type=FileStorage, location='files', required=True)
project_upload_parser.add_argument('unzip', type=bool, location='args', help="whether unzip")

project_upload_file_parser = script_project_parser.copy()
project_upload_file_parser.add_argument('files', type=list, location='json', required=True)
project_upload_file_parser.add_argument('comment', required=True)
project_upload_file_parser.add_argument('risk_level', type=int, required=False)
project_upload_file_parser.add_argument('unzip', type=bool, help="whether unzip or not")
project_upload_file_parser.add_argument('branch', type=str, help="operation branch")
project_upload_file_parser.add_argument('repository_type', type=str, required=True,
                                        help="project type, scripts/applications/configurations")

project_download_file_parser = reqparse.RequestParser()
project_download_file_parser.add_argument('id', type=int)

project_branch_parser = reqparse.RequestParser()
project_branch_parser.add_argument('name', required=True, help="branch name")

commit_diff_args = reqparse.RequestParser()
commit_diff_args.add_argument('branch', required=True, help='commit compare\' branch')


@ns.route('/project/<int:identifier>')
class Project(Resource):
    @ns.doc('list project file list based on path')
    @ns.expect(script_project_parser)
    @ns.marshal_list_with(script_model)
    def get(self, identifier):
        """Get project file list.

        Returns:
            .
        """
        args = script_project_parser.parse_args()
        app.logger.debug("get project file with params {}".format(args))
        try:
            repository_list = Repostiory().get_project_file_by_path(identifier, args)
        except ResourceNotFoundError as e:
            abort(404, e.msg)

        return repository_list

    @ns.doc('delete_repository')
    @ns.marshal_with(repository_fields, code=201)
    def delete(self, identifier):
        """Delete a gitlab project.

        Returns:
            The deleted project._attribute.
        """
        try:
            deleted_project = Repostiory().delete_project(identifier)
        except Error as e:
            app.logger.error("Deleted project {} failed".format(e.code))
            abort(e.code, e.msg)
        except GitlabError as e:
            app.logger.error("Gitlab Occur error: {}, project_id: {}".format(e.code, identifier))
            abort(e.code, e.msg)
        app.logger.info("Deleted project {} success".format(deleted_project))
        return deleted_project, 201


@ns.route('/project/<int:identifier>/info')
class ProjectInfo(Resource):
    @ns.doc('project info')
    @ns.marshal_list_with(repository_model)
    def get(self, identifier):
        """Get project info.

        Returns: project attributes
            .
        """
        app.logger.debug("get project info with params {}".format(identifier))
        try:
            info = Repostiory().get_project_by_id(identifier)
        except ResourceNotFoundError as e:
            abort(404, e.msg)
        return info.attributes


@ns.route('/project/<int:identifier>/file')
class ProjectFile(Resource):
    @ns.doc('script file content')
    @ns.expect(script_file_parser)
    @ns.marshal_with(script_repository_model)
    def get(self, identifier):
        """Get project file content
        Returns:
            project file info
        """
        args = script_file_parser.parse_args()
        app.logger.debug("get project file content with params {}".format(args))
        try:
            file_dict = Repostiory().get_project_file_content(identifier, args)
        except Error as e:
            app.logger.error("get project {} file failed, with params: {}, msg:{}".format(identifier, args, e.msg))
            abort(e.code, e.msg)
        return file_dict

    @ns.doc('create file & directory')
    @ns.expect(project_create_file)
    @ns.marshal_with(script_model, code=200)
    @passport_auth()
    def post(self, identifier):
        """Create project file or project directory

        Returns:
            Repostiory item
        """
        try:
            args = project_file_parser.parse_args()
            app.logger.debug("get project file with params {}".format(args))
            file_info = Repostiory().create_project_file(identifier, args)
        except Error as e:
            app.logger.error("create project {} file failed, with params: {}, msg:{}".format(identifier, args, e.msg))
            abort(e.code, e.msg)
        return file_info

    @ns.doc('script file update')
    @ns.expect(project_update_file)
    @ns.marshal_with(script_model, code=200)
    def put(self, identifier):
        """update the project file.

        Returns:
            the file of updated
        """
        args = project_file_update_args.parse_args()
        app.logger.debug("update script file with params {}".format(args))
        try:
            business_group = request.cookies.get('BussinessGroup')
            args.update(business_group=business_group)
            updated = Repostiory().update_project_file_content(identifier, args)
        except ResourceNotFoundError as e:
            app.logger.error("project id: {}, mgs: {}".format(identifier, e.msg))
            abort(e.code, e.msg)
        app.logger.info(u"update project file {}".format(updated))
        return updated


@ns.route('/project/<int:identifier>/commit')
class Commits(Resource):
    @ns.doc('list commits list')
    @ns.expect(project_commit_parser)
    @ns.marshal_list_with(project_commit_model)
    def get(self, identifier):
        """Get project commit, last/all_history/specified commit sha.
        Returns:
            .
        """
        args = project_commit_parser.parse_args()
        app.logger.debug("get project commit with params {}".format(args))
        commit_list = Repostiory().get_project_commit_list(identifier, args)
        return commit_list


# TODO: DELETE
@ns.route('/project/<int:identifier>/commit/<string:commit_sha>')
class Commit(Resource):
    @ns.doc('list files based on commit sha')
    @ns.param('commit_sha', 'commit sha value')
    @ns.expect(project_files_by_commit_args)
    @ns.marshal_list_with(project_file_model)
    def get(self, identifier, commit_sha):
        """Get project files by commit sha.
        Returns:
            .
        """
        try:
            args = project_files_by_commit_args.parse_args()
            path = args.path
            app.logger.debug("get project commit with params {}, {}, path: {}".format(identifier, commit_sha, path))
            file_list = Repostiory().get_project_files_by_commit(identifier, commit_sha, path)
        except Error as e:
            app.logger.error("get project id: {}, commit_sha: {}, mgs: {}".format(identifier, commit_sha, e.msg))
            abort(e.code, e.msg)
        return file_list


@ns.route('/project/<int:identifier>/diff/<string:commit_sha>')
class CommitDiffs(Resource):
    @ns.doc('list diff file content\'s based on commit sha and compare branch')
    @ns.expect(commit_diff_args)
    @ns.marshal_list_with(commit_diff_model)
    def get(self, identifier, commit_sha):
        """Get project commit, last/all_history/specified commit sha.
        Returns:
            .
        """
        args = commit_diff_args.parse_args()
        app.logger.debug("get project commit with params {}".format(args))
        branch = args.branch
        try:
            file_list = Repostiory().get_file_diffs_by_commit(identifier, commit_sha, branch)
        except Error as e:
            app.logger.error("get project id: {}, commit_sha: {}, diff's file failed. mgs: {}".
                             format(identifier, commit_sha, e.msg))
            abort(e.code, e.msg)
        except ResourceNotFoundError as e:
            app.logger.error("get project id: {}, commit_sha: {}, diff's file not found. mgs: {}".
                             format(identifier, commit_sha, e.msg))
            abort(e.code, e.msg)
        return file_list


@ns.route('/project/<int:identifier>/branches')
class Branches(Resource):
    @ns.doc('list branches list based on project_id')
    @ns.param('project_id', "project id")
    @ns.marshal_list_with(project_branch_return)
    def get(self, identifier):
        """Get project branches list.
        Returns:
            .
        """
        branch_list = Repostiory().get_project_branches_list(identifier)
        return branch_list

    @ns.doc('create branch')
    @ns.expect(project_create_branch)
    @ns.marshal_list_with(project_branch_return)
    @passport_auth()
    def post(self, identifier):
        """Create project branch.
        Returns:
            the branch of created.
        """
        args = project_branch_parser.parse_args()
        app.logger.debug("Delete branch item's params are: {}".format(args))
        try:
            branch = Repostiory().create_project_branch(identifier, args)
        except Error as e:
            app.logger.error("Create branch item's failed: {}".format(e.msg))
            abort(e.code, e.msg)
        return branch


@ns.route('/project/<int:identifier>/branch')
class Branches(Resource):
    @ns.doc('list branches list based on project_id')
    @ns.expect(project_branch_model)
    @ns.marshal_list_with(project_branch_return)
    @passport_auth()
    def delete(self, identifier):
        """Get project branches list.
        Returns:
            .
        """
        args = project_branch_parser.parse_args()
        app.logger.debug("Delete branch item's params are: {}".format(args))
        try:
            branch = Repostiory().delete_project_branch(identifier, args)
        except Error as e:
            app.logger.error("Delete branch item's failed: {}".format(e.msg))
            abort(e.code, e.msg)
        return branch


@ns.route('/project/<int:identifier>/files')
class FileSubmit(Resource):
    @ns.doc('project file or zip package upload info submit')
    @ns.expect(project_upload_file)
    @ns.marshal_with(script_model, code=200)
    def post(self, identifier):
        """submit the file's of the uploaded info.

        Returns:
            the file info of uploaded
        """
        args = project_upload_file_parser.parse_args()
        business_group = request.cookies.get('BusinessGroup', 'LDDS')
        args.update(business_group=business_group)
        app.logger.debug("upload script file/zip with params {}".format(args))
        try:
            updated = Repostiory().upload_files_submit(identifier, args)
        except Error as e:
            app.logger.error(u"{}".format(e.msg))
            abort(e.code, e.msg)
        except ValidationError as e:
            app.logger.error("Submit upload files failed, reason: {}".format(e.msg))
            abort(400, e.msg)

        app.logger.info("update script file {}".format(updated))
        return updated, 200

    @ns.doc('project files delete')
    @ns.expect(project_delete_file)
    @ns.marshal_list_with(script_model, code=200)
    @passport_auth()
    def delete(self, identifier):
        """Delete project's file

        Returns:
            the file of deleted
        """
        args = project_delete_file_parser.parse_args()
        app.logger.debug(u"delete project-id {} file with params {}".format(identifier, args))
        try:
            files = Repostiory.get_project_files(identifier, args)
            app.logger.info(u"Delete files items with args {},the files info is: {}".format(args, files))
        except ResourcesNotFoundError as e:
            app.logger.error(u"Project id {} , files can\'t be found with ids {}".format(identifier, args.ids))
            abort(404, e.message)
        try:
            Repostiory().delete_project_file(identifier, args)
        except GitlabNotFoundError as e:
            app.logger.error(u"Project id {}, msg: {}".format(identifier, e.message))
        except (ResourceNotEmptyError, GitlabError, Error) as e:
            app.logger.error(u"Project id {}, msg: {}".format(identifier, e.message))
            abort(e.code, e.message)
        return files, 200


@ns.route('/project/<int:identifier>/files/upload')
class FileUpload(Resource):
    @ns.doc('project file or zip package upload')
    @ns.expect(project_upload_parser)
    @ns.marshal_with(project_upload_return, code=200)
    def post(self, identifier):
        """upload the project files.

        Returns:
            the file info of upload
        """
        args = project_upload_parser.parse_args()
        app.logger.debug("upload script file/zip with params {}".format(args))
        try:
            updated = Repostiory.upload_project_file(identifier, args)
        except Error as e:
            app.logger.error(e.message)
            abort(e.code, e.msg)
        app.logger.info("update script file {}".format(updated))
        return updated, 200


@ns.route('/project/<int:identifier>/files/download')
class FileDownload(Resource):
    @ns.doc('project file or zip package download')
    @ns.expect(project_download_file_parser)
    def get(self, identifier):
        """download the project file.

        Returns:
            the file info of download
        """
        args = project_download_file_parser.parse_args()
        app.logger.debug("download script file/zip with params {}".format(args))
        try:
            file_content, file_name = Repostiory().download_project_file(identifier, args)
        except GitlabNotFoundError as e:
            app.logger.error(e.message)
            abort(e.code, e.message)
        return Response(file_content, mimetype="application/tar+gzip",
                        headers={"Content-disposition": "attachment;filename=aops_" + str(identifier) +
                                                        "{}".format(file_name)})

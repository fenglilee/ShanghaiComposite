#!/usr/bin/env python
# -*- coding:utf-8 -*-
from flask import current_app as app
from flask import abort, request
from flask_restplus import Resource, Model, fields, reqparse
from aops.applications.handlers.v1.common import time_util
from aops.applications.database.apis.repository.repository import Repostiory
from aops.applications.exceptions.exception import Error, ResourcesNotFoundError, ResourceAlreadyExistError, \
    ResourceNotFoundError, GitlabNotFoundError
from aops.applications.handlers.v1.repository import ns

repository_fields = Model('repository_fields', {
    'id': fields.Integer,
    'name': fields.String,
})

repository_create_fields = Model('repository_create', {
    'group_id': fields.Integer,
    'project_name': fields.String,
})

repository_delete_fields = Model('repository_delete', {
    'project_id': fields.Integer,
})

repository_model = Model('Repository', {
    'id': fields.Integer,
    'name': fields.String,
    'description': fields.String
})

repository_detail_model = Model('RepositoryList', {
    'id': fields.Integer,
    'name': fields.String,
    'description': fields.String,
    'created_at': fields.DateTime,
    'created_user': fields.String
})


language_model = Model('SystemLanguage', {
    'linux': fields.List(fields.Nested(repository_fields)),
    'windows': fields.List(fields.Nested(repository_fields))
})


script_repository_model = Model('Script', {
    'id': fields.String(),
    'file_id': fields.Integer(),
    'name': fields.String(required=True, description='The file\'s name'),
    'size': fields.Integer,
    'path': fields.String(required=True, description='The file path based on project /'),
    'branch': fields.String(required=False, description='The file\'s branch on project /'),
    'full_path': fields.String(required=True, description='The file full path based on project /'),
    'type': fields.String(required=True, default='blob', description='whether is directory or not'),
    'update_user': fields.String(required=True, description='The update user'),
    'project_id': fields.Integer(required=True, description='The script\'s project id'),
    'risk_level': fields.Integer(required=False, description='The script risk level'),
    'comment': fields.String(required=True, description='The script comment'),
    'content': fields.String(required=True, description='The script content'),
    'business_group': fields.String(required=False, description='The file\'s business group')
})


script_model = script_repository_model.clone("ScriptTime", time_util)

project_list_model = time_util.clone('ProjectListModel', {
    'file_id': fields.Integer(),
    'name': fields.String(required=True, description='The file\'s name'),
    'update_user': fields.String(required=True, description='The update user'),
    'project_id': fields.Integer(required=True, description='The script\'s project id'),
    'comment': fields.String(required=True, description='The script comment'),
    'business_group': fields.String(required=False, description='The file\'s business group')
})

script_version_model = Model('ScriptVersion', {
    'id': fields.Integer(),
    'script_id': fields.Integer(),
    'commit_sha': fields.String(),
    'version': fields.String(description='version based on time')
})

ns.add_model(repository_create_fields.name, repository_create_fields)
ns.add_model(repository_delete_fields.name, repository_delete_fields)
ns.add_model(repository_fields.name, repository_fields)
ns.add_model(repository_model.name, repository_model)
ns.add_model(project_list_model.name, project_list_model)
ns.add_model(language_model.name, language_model)
ns.add_model(repository_detail_model.name, repository_detail_model)

ns.add_model(script_version_model.name, script_version_model)
ns.add_model(script_repository_model.name, script_repository_model)
ns.add_model(script_model.name, script_model)

repository_group_parser = reqparse.RequestParser()
repository_group_parser.add_argument('group_id', type=str, required=True)

repository_parser = reqparse.RequestParser()
repository_parser.add_argument('project_name', type=str, required=True)
repository_parser.add_argument('group_id', type=int, required=True)

script_list_parser = reqparse.RequestParser()
script_list_parser.add_argument('id', type=int, required=True, help="project id ")
script_list_parser.add_argument("fq", type=str, location='args', dest="fuzzy_query")

pagination_args = reqparse.RequestParser()
pagination_args.add_argument('page', type=int, location='args', required=True, help='Current page number.')
pagination_args.add_argument("per_page", type=int, location='args', required=True, help='The number of items in a page.')
pagination_args.add_argument('fq', type=str, location='args', dest="fuzzy_query")


@ns.route('/')
class Repositories(Resource):
    """Repository Business Group list."""

    @ns.doc('list repository info based on group_name')
    @ns.marshal_list_with(repository_model)
    def get(self):
        """Get repository items base on repository group_name.

        Returns:
            Gitlab repository items dict.
        """
        try:
            group_list = Repostiory().get_repository_list()
            app.logger.info("Get repository's result is: {}".format(group_list))
        except Error as e:
            app.logger.error("Repository item can\'t be found with business group")
            abort(e.code, e.message)
        return group_list


@ns.route('/<string:group_name>/<string:repository_type>')
class Repository(Resource):
    """Repository Business Group list."""

    @ns.doc('list repository info based on group_name')
    @ns.param('group_id', 'The Repository\'s id')
    @ns.param('repository_type', 'The Repository\'s group type [scripts/applications/configurations/file_buckets]')
    @ns.marshal_list_with(repository_detail_model)
    def get(self, group_name, repository_type):
        """Get repository list base on repository group_id, repository_type.
        Returns:
            Gitlab repository items dict.
        """
        app.logger.debug("Get repository item with repository_type: {}".format(repository_type))
        try:
            sub_group = Repostiory().get_sub_repository_list(group_name, repository_type)
            app.logger.info("Get sub group item with id {} 's result is: {}".format(group_name, sub_group))
        except ResourceNotFoundError as e:
            app.logger.error("Repository item can\'t be found with repository_type {}".format(repository_type))
            abort(404, e.message)
        return sub_group


@ns.route('/project')
class Projects(Resource):
    @ns.doc('project list based on group_id')
    @ns.expect(repository_group_parser)
    @ns.marshal_list_with(project_list_model)
    def get(self):
        """Get project list base on repository group_name.

        Returns:
            Gitlab repository items dict.
        """
        try:
            args = repository_group_parser.parse_args()
            app.logger.debug("Get repository item with repository_type: {}".format(args))
            business_group = request.cookies.get('BusinessGroup', 'LDDS')
            sub_group = Repostiory().get_project_list(args, business_group)
            app.logger.info("Get sub group item with id {} 's result is: {}".format(args, sub_group))
        except ResourceNotFoundError as e:
            app.logger.error("Repository item can\'t be found with repository_type")
            abort(404, e.message)
        return sub_group

    @ns.doc('create_repository')
    @ns.expect(repository_create_fields)
    @ns.marshal_with(repository_fields)
    def post(self):
        """Create a gitlab project.

        Returns:
            The created project._attribute.
        """
        args = repository_parser.parse_args()
        app.logger.debug("Create gitlab project with params {}".format(args))
        try:
            created_project = Repostiory().create_project(args.project_name, args.group_id)
        except Error as e:
            app.logger.error("create project failed, args: {}, msg: {}".format(args, e.msg))
            abort(e.code, e.msg)
        except ResourceAlreadyExistError as e:
            app.logger.error("create project failed, args: {}, msg: {}".format(args, e.msg))
        app.logger.info("Created project {}".format(created_project))
        return created_project, 200


@ns.route('/system')
class SystemLanguage(Resource):
    """"""
    @ns.doc('list system language map to Gitlab')
    @ns.marshal_with(language_model)
    def get(self):
        """Get repository system language.

        Returns:
            Gitlab repository system language dict.
        """
        business_group = request.cookies.get('BussinessGroup', 'LDDS')
        try:
            system_language = Repostiory().get_script_system_language_map(business_group)
        except GitlabNotFoundError as e:
            abort(e.code, u"{}".format(e.message))
        app.logger.info("Get system language from Gitlab based on business group {}".format(system_language))
        return system_language


@ns.route('/script')
class RepositoryFiles(Resource):
    @ns.doc('script file list')
    @ns.expect(script_list_parser)
    @ns.marshal_list_with(script_model, code=200)
    def get(self):
        """get script list based on project id.

        Returns:
            the list info of scripts repository
        """
        args = script_list_parser.parse_args()
        app.logger.debug("script params {}".format(args))
        try:
            scripts_list = Repostiory.get_script_list(args)
        except ResourcesNotFoundError as e:
            app.logger.error("get script list: {} failed with parms: {}".format(scripts_list, args))
            abort(404, e.msg)
        app.logger.info("script list: {}".format(scripts_list))
        return scripts_list


@ns.route('/script/<int:identifier>')
class RepositoryFile(Resource):
    @ns.doc('script file list')
    @ns.marshal_list_with(script_version_model, code=200)
    def get(self, identifier):
        """get script version list.

        Returns:
            the list info of scripts version.
        """
        app.logger.debug("Get script id param is: {}".format(identifier))
        try:
            scripts_version_list = Repostiory.get_script_version_list(identifier)
        except ResourceNotFoundError as e:
            app.logger.error("get script list: {} failed with params: {}".format(scripts_version_list))
            abort(404, e.msg)
        app.logger.info("script list: {}".format(scripts_version_list))
        return scripts_version_list

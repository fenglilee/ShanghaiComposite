#!/usr/bin/env python
# -*- coding:utf-8 -*-
from flask_restplus import Resource, fields, Model, reqparse
from flask import abort, request, session, current_app as app
from aops.applications.handlers.v1.common import time_util, pagination_base_model
from aops.applications.database.apis.repository.risk_command import get_risk_repository_list, \
    delete_risk_repository_with_ids, update_risk_repository_with_id, create_risk_repository, \
    get_risk_repository_list_search
from aops.applications.database.apis.repository.risk_command import get_command_whitelist_list, \
    delete_command_whitelist_with_ids, update_command_whitelist_with_id, create_command_whitelist, get_whitelist_search

from aops.applications.exceptions.exception import ResourceNotFoundError, ResourcesNotFoundError, \
    ResourceAlreadyExistError

from aops.applications.handlers.v1.repository import ns
from aops.applications.handlers.v1.repository.repository import pagination_args

risk_commands_id_model = Model('RiskCommands', {
    'ids': fields.List(fields.Integer)
})

command_whitelist_without_id_model = Model('CommandWithoutId', {
    'comment': fields.String(required=True, description='The file\' risk statement'),
    'name': fields.String(required=True, description='The command white list\' name')
})


command_whitelist_model = time_util.clone('CommandWhiteList', {
    'id': fields.Integer(readOnly=True, description='The file\'s identifier'),
    'comment': fields.String(required=True, description='The file\' risk statement'),
    'creator': fields.String(description='The file\'s submitter'),
    'name': fields.String(required=True, description='The command white list\' name')
})

command_whitelist_pagination_model = pagination_base_model.clone("CommandWhiteListPagination", {
    "items": fields.List(fields.Nested(command_whitelist_model))
})

risk_repository_without_id_model = command_whitelist_without_id_model.clone('RiskRepositoryWithoutId', {
    'risk_level': fields.Integer(required=True, description='The task\'s risk level'),
})

risk_repository_model = command_whitelist_model.clone('RiskRepository', {
    'risk_level': fields.Integer(required=True, description='The task\'s risk level'),
})

risk_repository_pagination_model = pagination_base_model.clone("RiskRepositoryPagination", {
    "items": fields.List(fields.Nested(risk_repository_model))
})

ns.add_model(risk_commands_id_model.name, risk_commands_id_model)
ns.add_model(command_whitelist_model.name, command_whitelist_model)
ns.add_model(command_whitelist_without_id_model.name, command_whitelist_without_id_model)
ns.add_model(command_whitelist_pagination_model.name, command_whitelist_pagination_model)
ns.add_model(risk_repository_model.name, risk_repository_model)
ns.add_model(risk_repository_without_id_model.name, risk_repository_without_id_model)
ns.add_model(risk_repository_pagination_model.name, risk_repository_pagination_model)


risk_repository_list_args = pagination_args.copy()
risk_repository_list_args.add_argument('risk_level', type=str, location='args', choices=('1', '2', '3'))
risk_repository_list_args.add_argument('end_time', type=str, location='args')
risk_repository_list_args.add_argument('start_time', type=str, location='args')
risk_repository_list_args.add_argument('name', type=str, location='args')
risk_repository_list_args.add_argument('creator', type=str, location='args')
risk_repository_list_args.add_argument('fq', type=str, location='args')

risk_repository_command_whitelist_args = reqparse.RequestParser()
risk_repository_command_whitelist_args.add_argument('name', type=str)
risk_repository_command_whitelist_args.add_argument('creator', type=str)

risk_commands_id_args = reqparse.RequestParser()
risk_commands_id_args.add_argument('ids', type=list, location='json')

command_without_id_parser = reqparse.RequestParser()
command_without_id_parser.add_argument('name', type=str)
command_without_id_parser.add_argument('comment', type=str)

risk_without_id_parser = command_without_id_parser.copy()
risk_without_id_parser.add_argument('risk_level', type=int)


@ns.route('/risk')
class RiskRepositories(Resource):
    """Todo represent a resource in a RESTful app."""

    @ns.doc('list risk_repository')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'risk_repository list not found')
    @ns.expect(risk_repository_list_args)
    @ns.marshal_list_with(risk_repository_pagination_model)
    def get(self):
        """Get all risk_repository items."""
        args = risk_repository_list_args.parse_args()
        page = args.page
        per_page = args.per_page
        fq = args.fuzzy_query
        name = args.name
        risk_level = args.risk_level
        start_time = args.start_time
        end_time = args.end_time
        creator = args.creator

        app.logger.debug("Get risk_repository list's params are: {}".format(args))
        try:
            risks = get_risk_repository_list(page, per_page, fuzzy_query=fq, name=name, risk_level=risk_level,
                                             start_time=start_time, end_time=end_time, creator=creator)
            app.logger.info("Get Risk repository list's result with page num {}, and length is {}".
                            format(risks.page, len(risks.items)))
        except ResourcesNotFoundError as e:
            app.logger.error("Risk repository list can\'t be found with params: page={}, per_page={}".
                             format(page, per_page))
            abort(404, e.message)
        return risks

    @ns.doc('create_risk_repository')
    @ns.expect(risk_repository_without_id_model)
    @ns.marshal_with(risk_repository_model, code=200)
    def post(self):
        """Create a risk_repository items."""
        args = risk_without_id_parser.parse_args()
        app.logger.debug("Create item's params are: {}".format(args))
        try:
            user_info = session.get('user_info', {'user': 'admin'})
            creator = user_info.get('user')
            args.update(business_group=request.cookies.get('BusinessGroup', 'LDDS'))
            args.update(creator=creator)
            created_todo = create_risk_repository(args)
        except ResourceAlreadyExistError as e:
            app.logger.error(e.message)
            abort(409, e.message)
        app.logger.info("Created item's result is: {}".format(created_todo))
        return created_todo, 200

    @ns.doc('delete_risk_repository')
    @ns.response(200, 'RiskRepository deleted')
    @ns.expect(risk_commands_id_model)
    @ns.marshal_with(risk_repository_model)
    def delete(self):
        """Delete a given its identifier."""
        args = risk_commands_id_args.parse_args()
        app.logger.debug("Delete items with id: {}".format(args))
        try:
            deleted = delete_risk_repository_with_ids(args)
            app.logger.info("Delete risk_repository item with ids {},the risk_repository info is: {}".format(args, deleted))
        except ResourceNotFoundError as e:
            app.logger.error("item can\'t be found with id {}".format(args))
            abort(404, e.message)
        return deleted, 200


@ns.route('/risk/<int:identifier>')
@ns.response(404, 'RiskRepository not found')
@ns.param('identifier', 'The Risk repository\'s identifier')
class RiskRepository(Resource):
    """Show a single todo item and lets you update and delete them."""

    @ns.expect(risk_repository_without_id_model)
    @ns.response(200, 'risk_repository updated')
    @ns.marshal_with(risk_repository_model)
    def put(self, identifier):
        """Update a risk_repository given its identifier."""
        update_info = risk_without_id_parser.parse_args()
        app.logger.debug("Update risk_repository item with id: {}, and info is: {}".format(identifier, update_info))
        try:
            todo = update_risk_repository_with_id(identifier, update_info)
        except ResourceNotFoundError as e:
            app.logger.error("Risk_repository item can\'t be found with id {}".format(identifier))
            abort(404, e.message)
        app.logger.info("Update risk_repository item with id {},and latest info is: {}".format(identifier, todo.to_dict()))
        return todo, 200


@ns.route('/risk/search')
class RiskRepositorySearch(Resource):
    """Todo represent a resource in a RESTful app."""

    @ns.doc('list risk_repository')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'risk_repository list not found')
    @ns.expect(risk_repository_command_whitelist_args)
    @ns.marshal_list_with(risk_repository_model)
    def get(self):
        """Get all risk_repository items by search"""
        args = risk_repository_command_whitelist_args.parse_args()
        name = args.name
        creator = args.creator

        app.logger.debug("Get risk_repository list's params are: {}".format(args))
        try:
            risks = get_risk_repository_list_search(name=name, creator=creator)
            app.logger.info("Get Risk repository list's result, and result: {}".format(risks))
        except ResourcesNotFoundError as e:
            app.logger.error("Risk repository list can\'t be found with params: {}".
                             format(args))
            abort(404, e.message)
        return risks


@ns.route('/whitelist')
class CommandWhiteLists(Resource):
    """Todo represent a resource in a RESTful app."""

    @ns.doc('list risk_repository')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'Command whitelist not found')
    @ns.expect(risk_repository_list_args)
    @ns.marshal_list_with(command_whitelist_pagination_model)
    def get(self):
        """Get all Command_whitelist items."""
        args = risk_repository_list_args.parse_args()
        page = args.page
        per_page = args.per_page
        fq = args.fuzzy_query
        name = args.name
        start_time = args.start_time
        end_time = args.end_time
        creator = args.creator

        app.logger.debug("Get command whitelist list's params are: {}".format(args))
        try:
            risks = get_command_whitelist_list(page, per_page, fuzzy_query=fq, name=name,
                                               start_time=start_time, end_time=end_time, creator=creator)
            app.logger.info("Get Command whiteList list's result with page num {}, and length is {}".
                            format(risks.page, len(risks.items)))
        except ResourcesNotFoundError as e:
            app.logger.error("Command whitelist can\'t be found with params: page={}, per_page={}".
                             format(page, per_page))
            abort(404, e.message)
        return risks

    @ns.doc('create_command_whitelist')
    @ns.expect(command_whitelist_without_id_model)
    @ns.marshal_with(command_whitelist_model, code=200)
    def post(self):
        """Create a command_whitelist items."""
        args = command_without_id_parser.parse_args()
        app.logger.debug("Create item's params are: {}".format(args))
        try:
            user_info = session.get('user_info', {'user': 'admin'})
            creator = user_info.get('user')
            args.update(creator=creator)
            args.update(business_group=request.cookies.get('BusinessGroup', 'LDDS'))
            created_todo = create_command_whitelist(args)
        except ResourceAlreadyExistError as e:
            app.logger.error(e.message)
            abort(409, e.message)
        app.logger.info("Created item's result is: {}".format(created_todo))
        return created_todo, 200

    @ns.doc('delete_command_whitelist')
    @ns.response(200, 'Command_whitelist deleted')
    @ns.expect(risk_commands_id_model)
    @ns.marshal_with(command_whitelist_model)
    def delete(self):
        """Delete a given its identifier."""
        args = risk_commands_id_args.parse_args()
        app.logger.debug("Delete items with id: {}".format(args))
        try:
            deleted = delete_command_whitelist_with_ids(args)
            app.logger.info("Delete command_whitelist item with ids {},the todo info is: {}".format(args, deleted))
        except ResourceNotFoundError as e:
            app.logger.error("item can\'t be found with id {}".format(args))
            abort(404, e.message)
        return deleted, 200


@ns.route('/whitelist/<int:identifier>')
@ns.response(404, 'CommandWhiteList not found')
@ns.param('identifier', 'The CommandWhiteList\'s identifier')
class CommandWhiteLists(Resource):
    """CommandWhiteList item and lets you update."""

    @ns.expect(command_whitelist_without_id_model)
    @ns.response(200, 'command_whitelist updated')
    @ns.marshal_with(command_whitelist_model)
    def put(self, identifier):
        """Update a todo given its identifier."""
        update_info = command_without_id_parser.parse_args()
        app.logger.debug("Update command_whitelist item with id: {}, and info is: {}".format(identifier, update_info))
        try:
            todo = update_command_whitelist_with_id(identifier, update_info)
        except ResourceNotFoundError as e:
            app.logger.error("Command_whitelist item can\'t be found with id {}".format(identifier))
            abort(404, e.message)
        app.logger.info("Update item with id {},and latest info is: {}".format(identifier, todo.to_dict()))
        return todo, 200


@ns.route('/whitelist/search')
class WhiteListSearch(Resource):
    """Todo represent a resource in a RESTful app."""

    @ns.doc('list risk_repository')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'whitelist list not found')
    @ns.expect(risk_repository_command_whitelist_args)
    @ns.marshal_list_with(command_whitelist_model)
    def get(self):
        """Get all command whitelist items by search"""
        args = risk_repository_command_whitelist_args.parse_args()
        name = args.name
        creator = args.creator

        app.logger.debug("Get risk_repository list's params are: {}".format(args))
        try:
            risks = get_whitelist_search(name=name, creator=creator)
            app.logger.info("Get Command whitelist's result, and result: {}".format(risks))
        except ResourcesNotFoundError as e:
            app.logger.error("Command whitelist can\'t be found with params: {}".
                             format(args))
            abort(404, e.message)
        return risks

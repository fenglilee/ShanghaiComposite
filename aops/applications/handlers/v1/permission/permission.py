#!/usr/bin/env python
# -*- coding:utf-8 -*-
from flask_restplus import Resource, fields, Model, reqparse
from aops.applications.handlers.v1.common import pagination_base_model
from flask import session, abort, current_app as app
from aops.applications.database.apis.permission.permission import get_permission_list, get_permission_pagination_list
from aops.applications.exceptions.exception import ResourcesNotFoundError

from aops.applications.handlers.v1.permission import ns

permission_model = Model('Permission', {
    'id': fields.Integer(),
    'permission': fields.String(),
    'resource': fields.String(),
    'operation': fields.String(),
    'description': fields.String(),
})

# role_id_model = Model('RoleIdModel', {
#     'role_id': fields.Integer(readOnly=True, description='The role\'s identifier')
# })

permission_pagination_model = pagination_base_model.clone("PermissionPagination", {
    "items": fields.List(fields.Nested(permission_model))
})
ns.add_model(permission_model.name, permission_model)
# ns.add_model(role_id_model.name, role_id_model)
ns.add_model(permission_pagination_model.name, permission_pagination_model)

pagination_args = reqparse.RequestParser()
pagination_args.add_argument('page', type=int, location='args', required=True, help='Current page number.')
pagination_args.add_argument('fq', type=int, location='args', required=False, help='fq query')
pagination_args.add_argument("per_page", type=int, location='args', required=True,
                             help='The number of items in a page.')

role_id_parser = reqparse.RequestParser()
role_id_parser.add_argument('role_id', type=int, location='args', required=True)


@ns.route('/')
class Permissions(Resource):
    """Todo represent a resource in a RESTful app."""

    @ns.doc('list risk_repository')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'permission list not found')
    @ns.expect(role_id_parser)
    @ns.marshal_list_with(permission_model)
    def get(self):
        """Get all risk_repository items."""
        try:
            args = role_id_parser.parse_args()
            # user_info = session.get('user_info', {'permissions': []})
            # permissions = user_info.get('permissions')
            permissions = get_permission_list(role_id=args.role_id)
            app.logger.info("Get permission list's result, length is {}".format(len(permissions)))
        except ResourcesNotFoundError as e:
            app.logger.error("Permissions list can\'t be found")
            abort(404, e.message)
        return permissions


@ns.route('/pagination')
class PermissionPagination(Resource):
    """Todo represent a resource in a RESTful app."""

    @ns.doc('list risk_repository')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'permission list not found')
    @ns.expect(pagination_args)
    @ns.marshal_list_with(permission_pagination_model)
    def get(self):
        """Get permission items."""
        try:
            args = pagination_args.parse_args()
            page = args.page
            per_page = args.per_page
            fq = args.fq
            permissions = get_permission_pagination_list(page, per_page, fq)
            app.logger.info("Get permission list's result, page: {}, per_page: {}, length is {}".
                            format(page, per_page, len(permissions.items)))
        except ResourcesNotFoundError as e:
            app.logger.error("Permissions list can\'t be found")
            abort(404, e.message)
        return permissions

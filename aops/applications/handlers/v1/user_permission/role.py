#!/usr/bin/env python
# -*- coding:utf-8 -*-
from flask import current_app
from flask_restplus import Model, fields, reqparse, Resource, abort

from aops.applications.database.apis.user_permission.role import get_roles_list, create_role, get_role_with_id, delete_role_with_id, \
    update_role_with_id, list_roles
from aops.applications.database.apis.user_permission.role_permission import get_role_permissions, add_role_permissions, \
    delete_role_permissions
from aops.applications.exceptions.exception import ResourceNotFoundError
from aops.applications.exceptions.exception import ValidationError
from aops.applications.handlers.v1 import passport_auth
from aops.applications.handlers.v1.common import time_util
from aops.applications.handlers.v1.user_permission import ns
from aops.applications.handlers.v1.common import pagination_base_model



"""role"""
role_without_id_model = Model('RoleWithoutId', {
    'name': fields.String(required=True, description='The role\'s name'),
    'description': fields.String(required=True, description='The role\'s info')
})

role_model = role_without_id_model.clone('Role', time_util, {
    'id': fields.Integer(readOnly=True, description='The role\'s identifier'),
    'created_user': fields.String(required=True, description='The role\'s create user')
})

role_pagination_model = pagination_base_model.clone("role_pagination_model", {
    "items": fields.List(fields.Nested(role_model))
})

ns.add_model(role_pagination_model.name, role_pagination_model)
ns.add_model(role_without_id_model.name, role_without_id_model)
ns.add_model(role_model.name, role_model)

role_without_id_parser = reqparse.RequestParser()
role_without_id_parser.add_argument('name', type=str)
role_without_id_parser.add_argument('description', type=str)

role_parser = role_without_id_parser.copy()
role_parser.add_argument('id', type=int)
"""end role"""

"""permission"""
permission_without_id_model = Model('PermissionWithoutId', {
    'permission': fields.String(required=True, description='The permission\'s name'),
    'resource': fields.String(required=True, description='The resource_type\'s name'),
    'operation': fields.String(required=True, description='The operator\'s name'),
})

permission_model = permission_without_id_model.clone('Permission', time_util, {
    'id': fields.Integer(readOnly=True, description='The permission\'s identifier')
})

permission_pagination_model = pagination_base_model.clone("permission_pagination_model", {
    "items": fields.List(fields.Nested(permission_model))
})

ns.add_model(permission_without_id_model.name, permission_without_id_model)
ns.add_model(permission_model.name, permission_model)
ns.add_model(permission_pagination_model.name, permission_pagination_model)

permission_without_id_parser = reqparse.RequestParser()
permission_without_id_parser.add_argument('permission_name', type=str)
permission_without_id_parser.add_argument('resource_type_name', type=str)
permission_without_id_parser.add_argument('operator_name', type=str)

permission_parser = permission_without_id_parser.copy()
permission_parser.add_argument('id', type=int)
"""end permission"""

"""role_permission"""
role_permission_without_id_model = Model('RolePermissionWithoutId', {
    # 'permission_id': fields.Integer(description='The permission\'s ID'),
    # 'role_id': fields.Integer(description='The role\'s ID'),
    'permission_ids': fields.List(fields.Integer, readOnly=True, description='Multiple permission ids')
})

role_permission_model = role_permission_without_id_model.clone('RolePermission', time_util, {
    'id': fields.Integer(readOnly=True, description='The rolepermission\'s identifier')
})

ns.add_model(role_permission_without_id_model.name, role_permission_without_id_model)
ns.add_model(role_permission_model.name, role_permission_model)

role_permission_without_id_parser = reqparse.RequestParser()
role_permission_without_id_parser.add_argument('permission_ids', type=list, location='json')

role_list_args = reqparse.RequestParser()
role_list_args.add_argument("page", type=int, location='args', required=True, help='Current page number.')
role_list_args.add_argument("per_page", type=int, location='args', required=True, help='The number of items in a page.')

permission_list_args = reqparse.RequestParser()
permission_list_args.add_argument("page", type=int, location='args', required=True, help='Current page number.')
permission_list_args.add_argument("per_page", type=int, location='args', required=True, help='The number of items in a page.')


role_permission_parser = role_permission_without_id_parser.copy()
# role_permission_parser.add_argument('id', type=int)
"""end role_permission"""


@ns.route('/')
class Roles(Resource):
    """
    Shows a list of all roles, and lets you POST to add new tasks
    """
    @ns.doc('list_all_roles')
    @ns.marshal_with(role_pagination_model)
    @ns.expect(role_list_args)
    @passport_auth()
    def get(self):
        """
        List all roles
        """
        args = role_list_args.parse_args()
        current_app.logger.debug(u'Query roles with: {}'.format(args))
        try:
            roles = get_roles_list(**args)
            current_app.logger.info(u'Query roles succeed')
            return roles, 200
        except ResourceNotFoundError as e:
            current_app.logger.error(u'Query roles failed, reason: {}'.format(e.msg))
            abort(404, e.msg)

    @ns.doc('create_role')
    @ns.expect(role_without_id_model)
    @ns.marshal_with(role_model, code=201)
    @passport_auth()
    def post(self):
        """
        create a role
        :return:
        """
        args = role_parser.parse_args()
        current_app.logger.debug(u"Create role with params {}".format(args))
        try:
            created_role = create_role(args)
            current_app.logger.debug(u"Create role {}".format(created_role))
            return created_role, 201
        except ValidationError as e:
            current_app.logger.error(u'Create role failed, reason: {}'.format(e.msg))
            abort(404, e.msg)


@ns.route('/no-pagination')
class RolesNoPagination(Resource):
    """list all roles without pagination"""
    @ns.marshal_list_with(role_model)
    def get(self):
        current_app.logger.debug(u"get all roles began")
        try:
            roles = list_roles()
            current_app.logger.info(u"get all roles succeed")
            return roles
        except ValidationError as e:
            current_app.logger.error(u"get all roles failed, reason: {}".format(e.msg))


@ns.route('/<int:identifier>')
@ns.response(404, 'Role not found')
@ns.param('identifier', 'The role\'s identifier')
class Role(Resource):
    """Show a single role item and lets you delete them"""

    @ns.doc('delete_role')
    @ns.response(200, 'Role deleted')
    @ns.marshal_with(role_model)
    @passport_auth()
    def delete(self, identifier):
        """Delete a role given its identifier"""
        current_app.logger.debug(u'Delete role, role id is: {}'.format(identifier))
        try:
            result = delete_role_with_id(identifier)
            current_app.logger.info(u'Delete role succeed')
            return result, 200
        except (ResourceNotFoundError, ValidationError) as e:
            current_app.logger.error(u'Delete role failed, reason: {}'.format(e.msg))
            abort(404, e.msg)

    @ns.expect(role_without_id_model)
    @ns.response(200, 'role updated')
    @ns.marshal_with(role_model)
    @passport_auth()
    def put(self, identifier):
        """Update a role given its identifier"""

        role_update = role_without_id_parser.parse_args()
        current_app.logger.debug(u'Update role with: {}'.format(role_update))
        try:
            role = update_role_with_id(identifier, role_update)
            current_app.logger.info(u'Update role succeed')
            return role, 200
        except (ResourceNotFoundError, ValidationError) as e:
            current_app.logger.error(u'Update role failed, reason: {}'.format(e.msg))
            abort(404, e.msg)


# @ns.route('/permission/')
# class Permissions(Resource):
#     """
#     Shows a list of all permissions, and lets you POST to add new tasks
#     """
#     @ns.doc('list_all_permissions')
#     @ns.marshal_list_with(permission_model)
#     def get(self):
#         """
#         List all permissions
#         """
#         permissions = get_permission_list()
#         return permissions, 200


@ns.route('/role-permission/<int:role_id>')
@ns.response(404, 'Role not found')
@ns.param('role_id', 'The role\'s identifier')
class RolePermissions(Resource):
    """
    Operate the role's permission, add, delete, change, check.
    """
    @ns.doc('list all the permissions of a role')
    @ns.expect(permission_list_args)
    @ns.marshal_with(permission_pagination_model)
    def get(self, role_id):
        """
        Get all the permission of a role
        """
        args = permission_list_args.parse_args()
        current_app.logger.debug(u'Query permissions with: {}'.format(""))
        try:
            permissions = get_role_permissions(role_id, **args)
            current_app.logger.info(u'Query permissions succeed')
            return permissions, 200
        except Exception as e:
            current_app.logger.info(u'Query permissions failed, reason: {}'.format(e))
            abort(404, e.message)

    @ns.doc('add_role_permission')
    @ns.expect(role_permission_without_id_model)
    @ns.marshal_with(permission_model, code=201)
    @passport_auth()
    def post(self, role_id):
        """
        Add a permission to the role
        """
        args = role_permission_parser.parse_args()
        current_app.logger.debug(u'Create permission with: {}'.format(args))
        try:
            add_role_permission = add_role_permissions(role_id, args)
            current_app.logger.info(u'Create permission succeed')
            return add_role_permission, 201
        except ValidationError as e:
            current_app.logger.error(u'Create permission failed, reason: {}'.format(e.msg))
            abort(404, e.msg)

    @ns.doc('delete_role_permission')
    @ns.expect(role_permission_without_id_model)
    @ns.marshal_with(permission_model)
    @passport_auth()
    def delete(self, role_id):
        """
        Delete a permission of the role
        """
        args = role_permission_parser.parse_args()
        current_app.logger.debug(u'Delete permission with: {}'.format(args))
        try:
            delete_role_permission = delete_role_permissions(role_id, args)
            current_app.logger.info(u'Delete permission succeed')
            return delete_role_permission, 200
        except ValidationError as e:
            current_app.logger.error(u'Delete permission failed, reason: {}'.format(e.msg))
            abort(404, e.msg)


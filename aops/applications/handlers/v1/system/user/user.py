#!/usr/bin/env python
# -*- coding:utf-8 -*-

from flask import session
from flask import current_app as app
from flask_restplus.errors import abort
from flask_restplus import Namespace
from flask_restplus import Resource
from flask_restplus import fields
from flask_restplus import reqparse
from flask_restplus import Model
from aops.applications.database.apis import user as user_api
from aops.applications.database.apis.user_permission.user_role import get_user_roles
from aops.applications.database.apis.user_permission.user_role import add_user_roles
from aops.applications.database.apis.user_permission.user_role import delete_user_roles
from aops.applications.handlers.v1.user_permission.role import role_model
from aops.applications.exceptions.exception import ResourceNotFoundError
from aops.applications.exceptions.exception import ValidationError
from aops.applications.exceptions.exception import ResourcesNotFoundError
from aops.applications.exceptions.exception import Error
from aops.applications.handlers.v1.common import time_util
from aops.applications.handlers.v1.common import pagination_base_model
from aops.applications.handlers.v1 import passport_auth
from aops.applications.database.apis.system.user.user import gen_password_hash
from aops.applications.database.apis.system.user.user import PwdCheck
from aops.applications.database.apis.system.user.user import UsernameCheck



"""users"""

ns = Namespace('/v1/users', description='USER operations')

# define models
user_without_id_model = Model('UserWithoutId', {
    'username': fields.String(required=True, description='The user\'s name'),
    'password': fields.String(required=True, description='The user\'s password'),
    'realname': fields.String(required=True, description='The user\'s real name'),
    'business_ids': fields.List(fields.Integer, readOnly=True, description='The user\'s businesses'),
    'wechat': fields.String(required=True, description='The user\'s wechat'),
    'email': fields.String(required=True, description='The user\'s email'),
    'telephone': fields.String(required=True, description='The user\'s telephone'),
    'status': fields.Integer(required=True, description='The user\'s current status'),
    # 'modified_by': fields.String(required=True, description='The modifier\'s name'),
    'role_ids': fields.List(fields.Integer, readOnly=True, description='The roles identifiers')
})

user_model = user_without_id_model.clone("_user", time_util).clone('User', user_without_id_model, {
    'id': fields.Integer(readOnly=True, description='The user\'s identifier'),
    'business_names': fields.List(fields.String, readOnly=True, description='The user\'s businesse names'),
    'role_names': fields.List(fields.String, readOnly=True, description='The user\'s role names')
})

user_pagination_model = pagination_base_model.clone("UserPagination", {
    "items": fields.List(fields.Nested(user_model))
})

user_ids_model = Model('UserIds', {
    'user_ids': fields.List(fields.String, description='Multiple id of users')
})

# register models
ns.add_model(user_without_id_model.name, user_without_id_model)
ns.add_model(user_model.name, user_model)
ns.add_model(user_pagination_model.name, user_pagination_model)
ns.add_model(user_ids_model.name, user_ids_model)

# define request parsers
user_without_id_parser = reqparse.RequestParser()
user_without_id_parser.add_argument('username')
user_without_id_parser.add_argument('password')
user_without_id_parser.add_argument('realname')
user_without_id_parser.add_argument('wechat')
user_without_id_parser.add_argument('business_ids', type=list, location='json')
user_without_id_parser.add_argument('email')
user_without_id_parser.add_argument('telephone')
user_without_id_parser.add_argument('status')
user_without_id_parser.add_argument('modified_by')
user_without_id_parser.add_argument('role_ids', type=list, location='json')

user_parser = user_without_id_parser.copy()
user_parser.add_argument('id', type=int)

user_list_args = reqparse.RequestParser()
user_list_args.add_argument("page", type=int, location='args', required=True, help='Current page number.')
user_list_args.add_argument("per_page", type=int, location='args', required=True, help='The number of items in a page.')
user_list_args.add_argument('username', type=str, location='args', help='User name.')
user_list_args.add_argument('business', type=str, location='args')
user_list_args.add_argument('status', type=str, location='args')
user_list_args.add_argument('fuzzy_query', type=str, location='args')

user_ids_parser = reqparse.RequestParser()
user_ids_parser.add_argument('user_ids', type=list, location='json')
"""end users"""

"""user_constraint"""
user_constraint_without_id_model = Model('UserConstraintWithoutID', {
    'user_c_value': fields.String(required=True, description='The user_constraint\'s value'),
    'username':fields.String(required=True, description='The user\'s name'),
    'resource_name':fields.String(required=True, description='The resource\'s name'),
    'resource_c_value': fields.String(required=True, description='The resource_constraint\'s value'),
})

user_constraint_model = user_constraint_without_id_model.clone('UserConstraint', time_util, {
    'id': fields.Integer(readOnly=True, description='The user_constraint\'s identifier')
})

ns.add_model(user_constraint_without_id_model.name, user_constraint_without_id_model)
ns.add_model(user_constraint_model.name, user_constraint_model)

user_constraint_without_id_parser = reqparse.RequestParser()
user_constraint_without_id_parser.add_argument('user_c_value', type=str)
user_constraint_without_id_parser.add_argument('resource_c_value', type=str)
user_constraint_without_id_parser.add_argument('resource_name', type=str)
user_constraint_without_id_parser.add_argument('username', type=str)

user_constraint_parser = user_constraint_without_id_parser.copy()
user_constraint_parser.add_argument('id', type=int)
"""end user_constraint"""

"""user_role"""
user_role_without_id_model = Model('UserRoleWithoutId', {
    # 'user_id': fields.Integer(description='The user\'s userID'),
    'role_ids': fields.List(fields.Integer, readOnly=True, description='The roles identifiers')
})

user_role_model = user_role_without_id_model.clone('UserRole', time_util, {
    'id': fields.Integer(readOnly=True, description='The user role\'s identifier')
})

ns.add_model(user_role_without_id_model.name, user_role_without_id_model)
ns.add_model(user_role_model.name, user_role_model)

user_role_without_id_parser = reqparse.RequestParser()
user_role_without_id_parser.add_argument('user_id', type=int)
# user_role_without_id_parser.add_argument('role_id', type=int)
user_role_without_id_parser.add_argument('role_ids', type=str)

user_role_parser = user_role_without_id_parser.copy()
user_role_parser.add_argument('id', type=int)
"""end user_role"""

"""user password"""

user_password_model = Model('UserPassword', {
    'password': fields.String(required=True, description='The user\'s password'),
    'new_pwd': fields.String(required=True, description='The user\'s new password'),
    'verify_pwd': fields.String(required=True, description='The user\'s new password')
})

ns.add_model(user_password_model.name, user_password_model)

user_password_parser = reqparse.RequestParser()
user_password_parser.add_argument('password', type=str)
user_password_parser.add_argument('new_pwd', type=str)
user_password_parser.add_argument('verify_pwd', type=str)

"""end user password"""

"""users names"""
user_name_model = Model('UserNames', {
    'id': fields.Integer(description='The user\'s userID'),
    'realname': fields.String(description='The user\'s realname'),
    'username': fields.String(required=True, description='The user\'s username'),
})
ns.add_model(user_name_model.name, user_name_model)

"""end users names"""

"""users businesses"""
users_businesses_model = Model('users_businesses_model', {
    'id': fields.Integer,
    'name': fields.String,
    'description': fields.String
})
ns.add_model(users_businesses_model.name, users_businesses_model)
"""end users businessed"""


@ns.route('/')
class Users(Resource):
    """
    Shows a list of all user, and lets you POST to add new tasks
    """
    @ns.doc('list_users')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'User list not found')
    @ns.expect(user_list_args)
    @ns.marshal_list_with(user_pagination_model)
    @passport_auth()
    def get(self):
        """
        List all user with pagination and query
        """
        args = user_list_args.parse_args()
        page = args.page
        per_page = args.per_page
        username = args.username
        business = args.business
        status = args.status
        fuzzy_query = args.fuzzy_query
        app.logger.debug("User list's params are: {}".format(args))
        try:
            users = user_api.get_users_list(page, per_page,
                                            username=username, business=business, status=status,
                                            fuzzy_query=fuzzy_query)
            app.logger.info("User list's result with page num {}, and length is {}".format(users.page, len(users.items)))
            return users
        except ResourcesNotFoundError as e:
            app.logger.error("User list can\'t be found with params: page={}, per_page={}".format(page, per_page))
            abort(404, e.msg)

    @ns.doc('create_user')
    @ns.expect(user_without_id_model)
    @ns.marshal_with(user_model, code=201)
    @passport_auth()
    def post(self):
        """
        create a user
        """
        args = user_parser.parse_args()
        app.logger.debug("Create user with params {}".format(args))
        try:
            pwd_checker = PwdCheck()
            pwd_checker.validate_password(password=args.password)
            username_checker = UsernameCheck()
            username_checker.validate_username(username=args.username)
            created_user = user_api.create_user(args)
            if created_user == 403:
                abort(403, 'Already exist or some keys are not unique')
            app.logger.info("Created User {}".format(created_user))
            return created_user, 201
        except ValidationError as e:
            app.logger.error("Creating User failed, reason: {}".format(e.msg))
            abort(400, e.msg)
    
    @ns.doc('delete_users')
    @ns.expect(user_ids_model)
    @ns.marshal_list_with(user_model, code=200)
    @passport_auth()
    def delete(self):
        """
        delete multiple users
        """
        args = user_ids_parser.parse_args()
        app.logger.debug("Delete user item with user ids: {}".format(args.user_ids))
        try:
            deleted_users = user_api.delete_users_with_ids(args.user_ids)
            app.logger.info('Deleted users {}'.format(deleted_users))
            return deleted_users, 200
        except Error as e:
            app.logger.error('Deleting users fails, reason: {}'.format(e.msg))
            abort(403, 'Delete users')


@ns.route('/<int:identifier>')
@ns.response(404, 'User not found')
@ns.param('identifier', 'The user\'s identifier')
class User(Resource):
    """Show a single user item and lets you delete them"""

    @ns.doc('get_user')
    @ns.marshal_with(user_model)
    @passport_auth()
    def get(self, identifier):
        """Fetch a given user with identifier"""
        app.logger.debug(u"fetching user information begins by id: {}".format(identifier))
        try:
            user = user_api.get_user_with_id(identifier)
            app.logger.info(u"fetching user information completes by id: {}".format(identifier))
            return user
        except ResourceNotFoundError as e:
            app.logger.error(u"fetching user information fails, reason: {}".format(e.msg))
            abort(404, e.message)

    @ns.doc('delete_user')
    @ns.response(204, 'User deleted')
    @ns.marshal_with(user_model)
    @passport_auth()
    def delete(self, identifier):
        """Delete a user given its identifier"""
        app.logger.debug(u"deleting user begins, id: {}".format(identifier))
        try:
            user = user_api.get_user_with_id(identifier)
            user_api.delete_user_with_id(identifier)
            app.logger.info(u"deleting user completes, id: {}".format(identifier))
            return user, 204
        except ResourceNotFoundError as e:
            app.logger.error(u"deleting user fails, reason: {}".format(e.msg))
            abort(404, e.message)

    @ns.expect(user_without_id_model)
    @ns.marshal_with(user_model)
    @passport_auth()
    def put(self, identifier):
        """Update a user given its identifier"""
        user_info = user_without_id_parser.parse_args()
        app.logger.debug(u'updating user information begins, new user info: {}'.format(user_info))
        try:
            username_checker = UsernameCheck()
            username_checker.validate_username(username=user_info.username)
            user = user_api.update_user_with_id(identifier, user_info)
            app.logger.info(u'updating user information completes')
            return user, 201
        except (ResourceNotFoundError, ValidationError) as e:
            app.logger.error(u'updating user information fails, reason: {}'.format(e.msg))
            abort(404, e.message)


@ns.route('/<int:user_id>/user-role')
@ns.response(404, 'User not found')
@ns.param('user_id', 'The user\'s identifier')
class UserRoles(Resource):
    """
    Operate the user's role, add, delete, change, check.
    """
    @ns.doc('list all the roles of a user')
    @ns.marshal_list_with(role_model)
    def get(self, user_id):
        """
        Get all the roles of a user
        """
        app.logger.debug(u"fetching user roles begins, user id: {}".format(user_id))
        try:
            roles = get_user_roles(user_id)
            app.logger.info(u"fetching user roles completes, user id: {}".format(user_id))
            return roles, 200
        except ResourceNotFoundError as e:
            app.logger.error(u"fetching user roles fails, reason: {}".format(e.msg))
            abort(404, e.msg)

    @ns.doc('add_user_role')
    @ns.expect(user_role_without_id_model)
    @ns.marshal_with(role_model, code=201)
    @passport_auth()
    def post(self, user_id):
        """
        Add a role to the user
        """
        args = user_role_parser.parse_args()
        app.logger.debug(u'adding role to user begin')
        try:
            add_user_role = add_user_roles(user_id, args)
            if add_user_role == 403:
                abort(403, 'already exists')
            app.logger.info(u'adding role to user completes, role: {}, user id: {}'.format(args, user_id))
            return add_user_role, 201
        except ResourceNotFoundError as e:
            app.logger.error(u'adding role to user fails, reason: {}'.format(e.msg))
            abort(404, e.msg)

    @ns.doc('delete_user_role')
    @ns.expect(user_role_without_id_model)
    @ns.marshal_with(role_model)
    @passport_auth()
    def delete(self, user_id):
        """
        Delete a role of the user
        """
        args = user_role_parser.parse_args()
        app.logger.debug(u"deleting user role begins, user id: {}".format(user_id))
        try:
            delete_user_role = delete_user_roles(user_id, args)
            app.logger.info(u'deleting user role begins, user id: {}'.format(user_id))
            return delete_user_role, 200
        except ResourceNotFoundError as e:
            app.logger.info(u'deleting user role fails, reason: {}'.format(e.msg))
            abort(404, e.msg)


@ns.route('/<int:user_id>/user-password')
@ns.response(404, 'User not found')
@ns.param('user_id', 'The user\'s identifier')
class UserPassword(Resource):

    @ns.doc('direct to the password edit page')
    @ns.response(200, 'request success')
    @passport_auth()
    def get(self, user_id):
        """direct to the password edit page"""
        app.logger.debug(u'user check with id: {}'.format(user_id))
        try:
            user_api.get_user_with_id(user_id)
            app.logger.info(u'user check succeed by id: {}'.format(user_id))
            return 'ok', 200
        except ResourceNotFoundError as e:
            app.logger.error(u'user check fails, reason: {}'.format(e.msg))
            abort(404, e.message)

    @ns.doc('update user password')
    @ns.expect(user_password_model)
    @ns.response(200, 'request success')
    @ns.response(401, 'validation failed')
    @passport_auth()
    def post(self, user_id):
        """update user password """
        try:
            user = user_api.get_user_with_id(user_id)
            args = user_password_parser.parse_args()
            old_pwd_hash = gen_password_hash(args.password)
            new_pwd_hash = gen_password_hash(args.new_pwd)
            app.logger.debug(u"edit user password begin, old password: {}, new password: {}".format(old_pwd_hash, new_pwd_hash))

            if user.password != old_pwd_hash:
                raise ValidationError(u'Input password is not correct')
            if args.new_pwd != args.verify_pwd:
                raise ValidationError(u'The two passwords you enter do not match')
            if user.password == new_pwd_hash:
                raise ValidationError(u'The new password can not be the same as the old one')
            pass_checker = PwdCheck()
            pass_checker.validate_password(password=args.new_pwd)

            update_info = {
                'password': new_pwd_hash,
                'init_login': False
            }
            user.update(**update_info)
            session.pop('user_info', None)
            app.logger.info(u"user password has already been changed, old password: {}, new password: {}".format(old_pwd_hash, new_pwd_hash))
            return 'ok', 200
        except (ResourceNotFoundError, ValidationError) as e:
            app.logger.error(u"editing user password fails, reason: {}".format(e.msg))
            abort(404, e.msg)


@ns.route('/names')
class UsersNames(Resource):
    """
    list user names here
    """
    @ns.response(404, 'Users not found')
    @ns.marshal_list_with(user_name_model)
    def get(self):
        """
        get all users names
        """
        app.logger.debug(u"Query all users names begin")
        try:
            users = user_api.get_all_users()
            app.logger.info(u"Query all users names succeed")
            return users, 200
        except ResourceNotFoundError as e:
            app.logger.info(u"Query all users names failed, reason: {}".format(e.msg))


@ns.route('/<int:user_id>/businesses')
class UsersBusiness(Resource):
    """
    get user businesses
    """
    @ns.response(404, "Users not found")
    @ns.marshal_list_with(users_businesses_model)
    def get(self, user_id):
        app.logger.debug(u'get user businesses began')
        try:
            user = user_api.get_raw_user_with_id(user_id)
            businesses = user.businesses.all()
            app.logger.info(u'get user businesses succeed')
            return businesses, 200
        except ResourceNotFoundError as e:
            app.logger.error(u'get user businesses failed, reason: {}'.format(e.msg))
            abort(404, e.msg)




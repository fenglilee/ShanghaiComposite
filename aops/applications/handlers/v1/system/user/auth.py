from flask import session
from flask import current_app as app
from flask_restplus import Namespace, Resource, fields, reqparse, Model
from aops.applications.database.apis import user as user_api
from aops.applications.exceptions.exception import UserLoginError
from aops.applications.exceptions.exception import ValidationError

from flask_restplus.errors import abort


ns = Namespace('/v1/auth', description='User login and logout')


login_without_pwd_model = Model('LoginWithoutPwd', {
    'username': fields.String(required=True, description='The user\'s name')
 })

login_model = login_without_pwd_model.clone('Login', login_without_pwd_model, {
    'password': fields.String(required=True, description='The user\'s password')
})

login_response_model = Model('LoginResponse', {
    'id': fields.String(required=True, description='The user\'s id'),
    'username': fields.String(required=True, description='The user\'s name'),
    'init_login': fields.Boolean(required=True, description='The user\'s initial login flag')
})

ns.add_model(login_without_pwd_model.name, login_without_pwd_model)
ns.add_model(login_model.name, login_model)
ns.add_model(login_response_model.name, login_response_model)

login_parser = reqparse.RequestParser()
login_parser.add_argument('username', type=str)
login_parser.add_argument('password', type=str)


@ns.route('/login')
class Login(Resource):
    """
    User login
    """
    @ns.doc('user_login')
    @ns.expect(login_model)
    @ns.response(401, u'user login failed')
    @ns.marshal_with(login_response_model, code=201)
    def post(self):
        """
        User login
        """
        args = login_parser.parse_args()
        app.logger.debug(u"User login with params {}".format(args))
        try:
            user = user_api.check_user_password(args.username, args.password)
            privileges = [(role.name, permission.permission) for role in user.roles for permission in
                          role.permissions]
            roles = list(set(map(lambda item: item[0], privileges)))
            permissions = list(set(map(lambda item: item[1], privileges)))
            session['user_info'] = {
                'user': user.username,
                'roles': roles,
                'permissions': permissions
            }
            app.logger.info(u"User {} login successfully ".format(user.username))
            return user, 201
        except (UserLoginError, ValidationError) as e:
            app.logger.error(u"login failed, reason: {}".format(e.msg))
            abort(403, e.msg)


@ns.route('/logout')
class Logout(Resource):
    """
    User logout.
    """
    @ns.doc('user_logout')
    def get(self):
        """
        User logout
        """
        app.logger.debug(u'User logout, bye !!')
        try:
            session.pop('user_info', None)
            app.logger.info(u"User info in session after logout : {}".format(session))
            return 'ok', 201
        except KeyError as e:
            app.logger.error(u'User logout failed, reason: {}'.format(e))
            abort(401, '{}'.format(e))

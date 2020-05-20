#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 2018/7/26 19:09
# @Author  : szf

from flask import current_app as app
from flask_restplus import Namespace, Model, fields, reqparse, Resource, abort

from aops.applications.handlers.v1.common import time_util
from aops.applications.database.apis import message as message_apis
from aops.applications.exceptions.exception import ResourceNotFoundError, ResourceAlreadyExistError
from aops.applications.handlers.v1.common import pagination_base_model


ns = Namespace('/v1/messages', description='System Message')

# define models
message_without_id_model = Model('MessageWithoutID', {
    'created_at': fields.DateTime(description='Resource create time point'),
    'classify': fields.String(unique=False, description='The message classify'),
    'risk_level': fields.String(unique=False, description='The risk level of message'),
    'content': fields.String(unique=False, description='The message content'),
    'status': fields.String(unique=False, description='The message status')
})

message_model = message_without_id_model.clone('ApproveConfig', time_util, {
    'id': fields.Integer(readOnly=True, description='The message\'s identifier')
})

message_pagination_model = pagination_base_model.clone("message_pagination_model", {
    'items': fields.List(fields.Nested(message_model))
})

user_message_id_model = Model("user_message_id_model", {
    'user_id': fields.Integer(required=True, description='The user\'s identifier')
})
user_message_count_model = Model("user_message_count_model", {
    'username': fields.String(required=True, unique=False, description='present user\'s name'),
    'count': fields.Integer(required=True, description='The number of user\'s message')
})

# register models
ns.add_model(message_without_id_model.name, message_without_id_model)
ns.add_model(message_model.name, message_model)
ns.add_model(message_pagination_model.name, message_pagination_model)
ns.add_model(user_message_id_model.name, user_message_id_model)
ns.add_model(user_message_count_model.name, user_message_count_model)

# define parsers
message_without_id_parser = reqparse.RequestParser()
message_without_id_parser.add_argument('classify')
message_without_id_parser.add_argument('risk_level')
message_without_id_parser.add_argument('content')
message_without_id_parser.add_argument('status')
message_without_id_parser.add_argument('created_at')


message_query_params = reqparse.RequestParser()
message_query_params.add_argument("page", type=int, location='args', required=True, help='Current page number.')
message_query_params.add_argument("per_page", type=int, location='args', required=True, help='The number of items in a page.')
message_query_params.add_argument('start_time', type=str, location='args')
message_query_params.add_argument('end_time', type=str, location='args')
message_query_params.add_argument('type', type=str, location='args')
message_query_params.add_argument('risk_level', type=str, location='args')
message_query_params.add_argument('status', type=str, location='args')

user_message_params = reqparse.RequestParser()
user_message_params.add_argument("user_id", type=int, required=True, help='Current user id.', location='args')


@ns.route('/')
class Messages(Resource):
    """
     Show or create the system message
    """
    @ns.doc('Get system config')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'System message not found')
    @ns.expect(message_query_params)
    @ns.marshal_list_with(message_pagination_model)
    def get(self):
        """
        Get system message item
        Return:
            the system message item
        """
        args = message_query_params.parse_args()
        app.logger.debug("Query system message args {}".format(args))
        try:
            messages = message_apis.get_message_list(**args)
            app.logger.info("Get system message with {}".format(args))
            return messages, 200
        except ResourceNotFoundError as e:
            app.logger.error("No found the list of system messages")
            abort(404, e.message)

    @ns.doc('create a system message')
    @ns.expect(message_without_id_model)
    @ns.marshal_with(message_model, code=201)
    def post(self):
        """
        create  a system message item
        Returns:
            the new system message item
        """

        args = message_without_id_parser.parse_args()
        data = {
            'classify': args.classify,
            'risk_level': args.risk_level,
            'content': args.content,
            'status': args.status,
            'users': args.usernames,
        }
        app.logger.debug("Create system message with params {}".format(args))

        try:
            message = message_apis.create_message(**data)
            app.logger.info("Create system message {}".format(message))
            # return message, 201
        except ResourceAlreadyExistError as e:
            app.logger.error(e.message)
            abort(409, 'Already exist')


@ns.route('/user-count')
class MessagesCount(Resource):
    """count user message"""

    @ns.response(404, "Messages not found")
    @ns.expect(user_message_params)
    @ns.marshal_with(user_message_count_model)
    def get(self):
        args = user_message_params.parse_args()
        identifier = args.user_id
        app.logger.debug(u'Count user message began')
        try:
            res = message_apis.count_user_message(identifier)
            app.logger.info(u'Count user message succeed')
            return res, 200
        except ResourceNotFoundError as e:
            app.logger.error(u'Count user message failed, reason: {}'.format(e.msg))
            abort(404, "Messages not found")


@ns.route('/<int:identifier>')
class MessageUpdate(Resource):
    """message detail here"""

    @ns.doc(u"update message here")
    @ns.expect(message_without_id_model)
    @ns.marshal_with(message_model)
    def put(self, identifier):
        args = message_without_id_parser.parse_args()
        app.logger.debug(u"Updating message with: {}".format(args))
        try:
            message = message_apis.update_message(identifier, **args)
            app.logger.info(u"Updating message succeed")
            return message, 200
        except ResourceNotFoundError as e:
            app.logger.error(u"Updating message failed, reason: {}".format(e.msg))
            abort(404, e.msg)


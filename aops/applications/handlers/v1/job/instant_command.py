#!/usr/bin/env python
# -*- coding:utf-8 -*-
from flask import current_app, abort
from flask_restplus import Namespace, Model, fields, reqparse, Resource
from aops.applications.database.apis.job.instant_command import get_instant_command_record, \
    carry_out_command
from aops.applications.exceptions.exception import SchedulerError, NotCommandWhiteListError, MismatchError
from aops.applications.handlers.v1.common import full_time_util, pagination_base_model

ns = Namespace('/v1/command', description='Instant command operations')

command_without_id_model = Model('CommandWithoutID', {
    'target_ip': fields.String,
    'execution_account': fields.String,
    'command': fields.String(required=False),
})

command_model = command_without_id_model.clone('Command', full_time_util, {
    'id': fields.Integer(readOnly=True),
    'execution_id': fields.String(required=False),
    'end_time': fields.DateTime(required=False),
    'time': fields.String(required=True),
})

command_pagination_model = pagination_base_model.clone('CommandPagination', {
    'items': fields.List(fields.Nested(command_model))
})

carry_out_result_without_id_model = Model('CarryOutResultWithoutID', {
    'execution_id': fields.String,
    'target_ip': fields.String,
})

carry_out_result_model = carry_out_result_without_id_model.clone('CarryOutResult', {
    'result': fields.String()
})

ns.add_model(command_without_id_model.name, command_without_id_model)
ns.add_model(command_model.name, command_model)
ns.add_model(command_pagination_model.name, command_pagination_model)
ns.add_model(carry_out_result_without_id_model.name, carry_out_result_without_id_model)
ns.add_model(carry_out_result_model.name, carry_out_result_model)

command_without_id_parser = reqparse.RequestParser()
command_without_id_parser.add_argument('target_ip', type=list, location='json')
command_without_id_parser.add_argument('command')
command_without_id_parser.add_argument('execution_account')

command_list_args = reqparse.RequestParser()
command_list_args.add_argument('page', type=int, location='args', required=True, help='Current page number.')
command_list_args.add_argument('per_page', type=int, location='args', required=True, help='The number of items in a page.')
command_list_args.add_argument('creator', location='args')
command_list_args.add_argument('ip', location='args')


carry_out_result_parser = reqparse.RequestParser()
carry_out_result_parser.add_argument('execution_id', location='json')
carry_out_result_parser.add_argument('target_ip', location='json')


@ns.route('/')
class Commands(Resource):
    """
    Shows a list of all instant commands, and lets you POST to add new instant commands
    """
    @ns.doc('list_all_instant_commands')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'instant commands list not found')
    @ns.marshal_list_with(command_pagination_model)
    def get(self):
        """
        list all instant commands
        Returns:
            all instant commands
        """
        args = command_list_args.parse_args()
        page = args.page
        per_page = args.per_page
        ip = args.ip

        current_app.logger.debug("Get instant commands list's params are: {}".format(args))
        try:
            instant_command = get_instant_command_record(page, per_page, ip)
            current_app.logger.info("Get instant commands list's result with page num {}, and length is {}".format(instant_command['page'], len(instant_command['items'])))
        except SchedulerError as e:
            current_app.logger.error("instant command list can\'t be found with params: page={}, per_page={}".format(page, per_page))
            abort(404, e.message)
        return instant_command

    @ns.doc('carry_out_instant_command')
    @ns.expect(command_without_id_model)
    @ns.marshal_with(command_model)
    def post(self):
        """
        carry out a instant command
        Returns:
            the instant command items
        """
        args = command_without_id_parser.parse_args()
        current_app.logger.debug("carry out a instant command params are: {}".format(args))
        try:
            result = carry_out_command(args)
        except SchedulerError as e:
            abort(404, e.message)
        except NotCommandWhiteListError as e:
            abort(404, e.message)
        except MismatchError as e:
            abort(404, e.message)
        current_app.logger.info("carry out instant command item's result is: {}".format(result))
        return result

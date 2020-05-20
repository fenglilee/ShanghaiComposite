#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 2018/7/28 13:24
# @Author  : szf


from flask import current_app as app
from flask_restplus import Namespace, Model, fields, reqparse, Resource, abort

from aops.applications.handlers.v1.common import full_time_util, time_util, pagination_base_model
from aops.applications.database.apis import process_execution, process_execution_record as exec_record
from aops.applications.exceptions.exception import ResourceNotFoundError, ResourcesNotFoundError, ResourceAlreadyExistError, Error

ns = Namespace('/v1/instant-processes', description='Instant processes operations')

EXECUTION_TYPE = 'instant'
##############################################
#
# define models
#
###############################################
instant_process_without_id_model = Model('InstantProcessWithoutID', {
    'process_id': fields.Integer(readOnly=True, description='The process\'s identifier used to create instant process')
})

instant_process_model = instant_process_without_id_model.clone('InstantProcess', full_time_util, {
    'id': fields.Integer(readOnly=True, description='The process\'s identifier'),
    'name': fields.String(required=True, description='The instant process\'s name'),
    'description': fields.String(required=True, description='The instant process\'s description'),
    'status': fields.Integer(required=True, default=0, description='Is this instant process enabled'),
    'scheduling': fields.String(required=True, description='The instant process\'s scheduling including the job/tasks'),
    'business_group': fields.String(required=True, description='The process\'s business group'),
    'has_manual_job': fields.Integer(required=True, default=0, description='Is there manul job or not'),
    'creator': fields.String(required=True, description='The instant process\'s creator'),
    'execution_type': fields.String(required=True, description='The process\'s execution type'),
    'execution_account': fields.Integer(required=True, description='The instant process\'s execution account'),
    'risk_level': fields.Integer(required=True, description='The process\'s risk level'),
    'success_rate': fields.Integer(required=False, default=0, description='The process\'s success rate'),

    'timed_type': fields.String(required=True, description='The instant timed type for instant process'),
    'timed_config': fields.String(required=True, description='The timed config for timed process'),
    'timed_date': fields.String(required=True, description='The timed date for timed process'),
    'timed_expression': fields.String(required=True, description='The timed expression for timed process'),
})

instant_process_ids_model = Model('InstantProcessIds', {
    'process_ids': fields.List(fields.Integer, description='Multiple ids of instant processs')
})

instant_process_ids_status_model = instant_process_ids_model.clone('InstantProcessIdsStatus', {
    'status': fields.Integer(required=True, description='Are these instant processes enabled')  # 0: disabled 1: enabled
})

instant_process_pagination_model = pagination_base_model.clone('ProcessPagination', {
    'items': fields.List(fields.Nested(instant_process_model))
})

instant_process_update_model = Model('InstantProcessUpdate', {
    'scheduling': fields.String(required=True, description='The process\'s name'),
})

execution_model = Model('InstantExecution', {
    'process_info': fields.String(required=False),
})

continue_execution_model = Model('TimedExecution', {
    'execution_id': fields.String(required=False),
})

execution_result_model = Model('InstantExecutionResult', {
    'execution_id': fields.String(required=True)
})

execution_record_without_id_model = Model('InstantExecutionRecordWithoutId', {
    'execution_id': fields.String(required=True, description='The execution id process from scheduler'),
    'name': fields.String(required=True, description='The process\'s name'),
    'execution_status': fields.Integer(required=True, default=0, description='The execution status for the process'),
    'start_time': fields.String(required=True, description='The process\'s start time for execution'),
    'end_time': fields.String(required=True, description='The process\'s end time for execution'),
    'result': fields.String(readOnly=True, description='The execution result of instant process'),
    'scheduling': fields.String(required=True, description='The process\'s scheduling including the job/tasks'),
    'business_group': fields.String(required=True, description='The process\'s business group'),
    'time': fields.String(),
    'process_execution_id': fields.Integer(required=True, description='The process execution instance identifier')
})

execution_record_model = execution_record_without_id_model.clone('InstantExecutionRecord', full_time_util, {
    'id': fields.Integer(readOnly=True, description='The process\'s identifier'),
    'executor': fields.String(required=True, description='The process\'s executor'),
    'creator': fields.String(required=True, description='The process\'s creator'),
    'execution_type': fields.String(required=True, description='The process\'s execution type')
})

execution_record_pagination_model = pagination_base_model.clone('InstantExecutionRecordPagination', {
    'items': fields.List(fields.Nested(execution_record_model))
})

##############################################
#
#  register models
#
###############################################
ns.add_model(instant_process_without_id_model.name, instant_process_without_id_model)
ns.add_model(instant_process_model.name, instant_process_model)
ns.add_model(instant_process_ids_model.name, instant_process_ids_model)
ns.add_model(instant_process_ids_status_model.name, instant_process_ids_status_model)
ns.add_model(instant_process_pagination_model.name, instant_process_pagination_model)
ns.add_model(instant_process_update_model.name, instant_process_update_model)

ns.add_model(execution_model.name, execution_model)
ns.add_model(execution_result_model.name, execution_result_model)

ns.add_model(execution_record_without_id_model.name, execution_record_without_id_model)
ns.add_model(execution_record_model.name, execution_record_model)
ns.add_model(execution_record_pagination_model.name, execution_record_pagination_model)
ns.add_model(continue_execution_model.name, continue_execution_model)

##############################################
#
# define request parsers
#
###############################################
process_ids_parser = reqparse.RequestParser()
process_ids_parser.add_argument('process_ids', type=list, location='json')

instant_process_list_args = reqparse.RequestParser()
instant_process_list_args.add_argument('page', type=int, location='args', required=True, help='Current page number.')
instant_process_list_args.add_argument('per_page', type=int, location='args', required=True, help='The number of items in a page.')

instant_process_without_id_parser = reqparse.RequestParser()
instant_process_without_id_parser.add_argument('process_id', type=int)

# instant_process_parser = instant_process_without_id_parser.copy()
# instant_process_parser.add_argument('id', type=int)
# instant_process_parser.add_argument('risk_level', type=int)
# instant_process_parser.add_argument('success_rate', type=int)
# instant_process_parser.add_argument('name')
# instant_process_parser.add_argument('description')
# instant_process_parser.add_argument('status')
# instant_process_parser.add_argument('scheduling')
# instant_process_parser.add_argument('has_manual_job', type=int)

instant_process_ids_status_parser = process_ids_parser.copy()
instant_process_ids_status_parser.add_argument('status', type=int)  # 0: disabled 1: enabled

instant_process_update_parser = reqparse.RequestParser()
instant_process_update_parser.add_argument('scheduling')


execution_parser = reqparse.RequestParser()
execution_parser.add_argument('process_info')

continue_execution_parser = reqparse.RequestParser()
continue_execution_parser.add_argument('execution_id')

#
# execution_record_without_id_parser = reqparse.RequestParser()
# execution_record_without_id_parser.add_argument('name')
# execution_record_without_id_parser.add_argument('execution_id')
# execution_record_without_id_parser.add_argument('execution_status')
# execution_record_without_id_parser.add_argument('start_time')
# execution_record_without_id_parser.add_argument('end_time')
# execution_record_without_id_parser.add_argument('scheduling')
# execution_record_without_id_parser.add_argument('business_group')
# execution_record_without_id_parser.add_argument('result')
# execution_record_without_id_parser.add_argument('process_execution_id')
#

execution_record_list_args = reqparse.RequestParser()
execution_record_list_args.add_argument('page', type=int, location='args', required=True, help='Current page number.')
execution_record_list_args.add_argument('per_page', type=int, location='args', required=True, help='The number of items in a page.')
execution_record_list_args.add_argument('start_time', location='args')
execution_record_list_args.add_argument('end_time', location='args')

##################################################
#
# Instant process related resources
#
###################################################
@ns.route('/')
class InstantProcesses(Resource):
    """
    Show a list of instant process, create a new instant process and delete or update multiple instant process
    """
    @ns.doc('list all instant processes')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'Process list not found')
    @ns.expect(instant_process_list_args)
    @ns.marshal_list_with(instant_process_pagination_model)
    def get(self):
        """
        Get the instant process items list.
        Return:
             the instant process items list
        """
        args = instant_process_list_args.parse_args()

        app.logger.debug("Get instant process list's params are: {}".format(args))

        try:
            instant_process = process_execution.get_process_execution_list(EXECUTION_TYPE, args.page, args.per_page)
            app.logger.info("Get instant process list's result with page num {},and length is {}".
                            format(args.page, len(instant_process.items)))
        except ResourcesNotFoundError as e:
            app.logger.error("Processes list can\'t be found with params: page={}, per_page={}".\
                             format(args.page, args.per_page))
            abort(404, e.message)
        return instant_process

    @ns.doc('create instant process')
    @ns.expect(instant_process_without_id_model)
    @ns.marshal_with(instant_process_model, code=200)
    def post(self):
        """
        Create a instant process item
        Return:
            the new instant process item
        """
        args = instant_process_without_id_parser.parse_args()
        args.execution_type = EXECUTION_TYPE
        app.logger.debug("Create instant process item's params are: {}".format(args))
        try:
            created_process = process_execution.create_process_execution(args)
        except ResourceAlreadyExistError as e:
            app.logger.error("{} this instant process already exists".format(args))
            abort(403, 'Already exists')
        app.logger.info("Created instant process item's result is: {}".format(created_process))

        return created_process

    @ns.doc('delete multiple instant processes')
    @ns.expect(instant_process_ids_model)
    @ns.marshal_with(instant_process_model, code=201)
    def delete(self):
        """
        Delete multiple instant process items
        Return:
            the deleted instant process items
        """
        args = process_ids_parser.parse_args()
        app.logger.debug("Delete instant process item with instant process ids: {}".format(args))
        try:
            deleted_processes = process_execution.delete_process_execution_with_ids(args.process_ids)
        except Error as e:
            app.logger.error('Delete processes')
            abort(403, 'Delete processes')
        app.logger.debug('Deleted processes {} '.format(deleted_processes))

        return deleted_processes, 200

    @ns.doc('enable or disable instant processes')
    @ns.expect(instant_process_ids_status_model)
    @ns.marshal_with(instant_process_model, code=201)
    def put(self):
        """
        Enable or disable multiple instant process
        Return:
            the operational instant process
        """
        args = instant_process_ids_status_parser.parse_args()
        try:
            updated_processes = process_execution.update_status_with_ids(args.process_ids, args.status)
        except Error as e:
            app.logger.error('Update status for processes', e.message)
            abort(403, 'Update processes')
        app.logger.debug('Update processes {} '.format(updated_processes))

        return updated_processes, 200


@ns.route('/<int:identifier>')
@ns.response(404, 'Process not found')
@ns.param('identifier', 'The instant process\'s identifier')
class InstantProcess(Resource):
    """
    Show a single process, delete and update it.
    """
    @ns.doc('Get single process item')
    @ns.marshal_with(instant_process_model)
    @ns.response(200, 'Get single process item')
    def get(self, identifier):
        """
        Get a given process with identifier
        Args:
            identifier: process id
        Return:
            the process item
        """
        app.logger.debug("Get a process item with id: {}".format(identifier))
        try:
            process = process_execution.get_process_execution_with_id(identifier)
            app.logger.info("Get process item with id {} 's result is: {}".format(identifier, process.to_dict()))
        except ResourceNotFoundError as e:
            app.logger.error("process item can\'t be found with id {}".format(identifier))
            abort(404, e.message)
        return process

    @ns.doc('Update single process item')
    @ns.expect(instant_process_update_model)
    @ns.response(200, 'Timed process updated')
    @ns.marshal_with(instant_process_model)
    def put(self, identifier):
        """
        Update a given process with identifier
        Args:
            identifier: process id
        Return:
            the updated process item
        """
        args = instant_process_update_parser.parse_args()
        app.logger.debug("update process with params {}, identifier {}".format(args, identifier))
        try:
            updated_process = process_execution.update_process_execution_with_id(identifier, args)
            app.logger.debug("update process {}".format(updated_process))
        except ResourceNotFoundError as e:
            app.logger.error("No found updated process with identifier {}".format(identifier))
            abort(404, e.message)

        return updated_process


@ns.route('/execution')
class Execution(Resource):
    """
    Send a request to scheduler and execut an instant process
    """
    @ns.doc('Execute a instant process')
    @ns.expect(execution_model)
    @ns.marshal_list_with(execution_result_model)
    def post(self):
        """execute a instant process"""
        args = execution_parser.parse_args()
        app.logger.debug("execute instant process item's params are: {}".format(args))
        result = process_execution.execute_process(EXECUTION_TYPE, args.process_info)
        # handle the result
        if result == 409:
            abort(409, 'executing process ...')
        if result == 404:
            abort(404, 'fail to executing process :(')
        app.logger.info("execute instant process item's result is: {}".format(result))
        return result

@ns.route('/continue-execution')
class ContinueExecution(Resource):
    """
    Send a request to scheduler and execut an instant process
    """
    @ns.doc('Execute a instant process')
    @ns.expect(continue_execution_model)
    @ns.marshal_list_with(execution_result_model)
    def post(self):
        """execute a instant process"""
        args = continue_execution_parser.parse_args()
        app.logger.debug("execute timed process item's params are: {}".format(args))
        result = process_execution.continue_execute_process(EXECUTION_TYPE, args.execution_id)
        app.logger.info("execute timed process item's result is: {}".format(result))
        return result


@ns.route('/stop')
class StopProcess(Resource):
    """
    Send a request to scheduler and stop an instant process
    """
    @ns.doc('Stop a instant process')
    @ns.expect(continue_execution_model)
    @ns.marshal_list_with(execution_result_model)
    def post(self):
        """stop a instant process"""
        args = continue_execution_parser.parse_args()
        app.logger.debug("stop process item's params are: {}".format(args))
        result = process_execution.stop_process(args.execution_id)
        app.logger.info("stop process item's result is: {}".format(result))
        return result


@ns.route('/execution-records')
class ExecutionRecords(Resource):
    """
    Shows a list of all execution record
    """

    @ns.doc('list_all_execution_record')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'execution record list not found')
    @ns.marshal_list_with(execution_record_pagination_model)
    @ns.expect(execution_record_list_args)
    # @passport_auth()
    def get(self):
        """
        list all execution record
        Returns:
            all execution record
        """
        args = execution_record_list_args.parse_args()
        page = args.page
        per_page = args.per_page
        start_time = args.start_time
        end_time = args.end_time

        app.logger.debug("Get execution record list's params are: {}".format(args))
        try:
            execution_record = exec_record.get_execution_record_list(EXECUTION_TYPE, page, per_page,
                                                                     start_time=start_time,
                                                                     end_time=end_time)
            app.logger.info("Get execution record list's result {}".format(execution_record))
            # app.logger.info("Get execution record list's result with page num {}, and length is {}".format(
            #     execution_record.page, len(execution_record.items)))
        except ResourcesNotFoundError as e:
            app.logger.error(
                "execution record list can\'t be found with params: page={}, per_page={}".format(page, per_page))
            abort(404, e.message)
        return execution_record

    # @ns.doc('create process execution record')
    # @ns.expect(execution_record_without_id_model)
    # @ns.marshal_with(execution_record_model, code=200)
    # def post(self):
    #     """
    #     Create a execution record item
    #     Return:
    #         the new execution record item
    #     """
    #     args = execution_record_without_id_parser.parse_args()
    #     args.execution_type = EXECUTION_TYPE
    #     app.logger.debug("Create process execution record item's params are: {}".format(args))
    #     try:
    #         record = exec_record.create_execution_record(EXECUTION_TYPE, args)
    #     except ResourceAlreadyExistError as e:
    #         app.logger.error(u"{} this process execution record already exists".format(record.name))
    #         abort(403, 'Already exists')
    #     app.logger.info(u"Created process execution record item's result is: {}".format(record))
    #
    #     return record
    #





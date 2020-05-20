#!/usr/bin/env python
# -*- coding:utf-8 -*-
from flask import current_app
from flask_restplus import Namespace, Model, fields, reqparse, Resource, abort

from aops.applications.database.apis.job.daily_inspection import get_daily_job_result_list, get_daily_host_result_list
from aops.applications.exceptions.exception import ResourcesNotFoundError, SchedulerError
from aops.applications.handlers.v1.common import full_time_util, pagination_base_model
from aops.applications.handlers.v1.job.job import execution_record_pagination_model, job_record_pagination_model

ns = Namespace('/v1/daily', description='Daily inspection operations')

daily_without_id_model = Model('DailyWithoutID', {
    'name': fields.String(required=True),
    'description': fields.String(required=True),
    'system_type': fields.String(required=True),
    'target_ip': fields.String,
    'item': fields.String(required=True),
    'result': fields.String(required=True),
    'business_group': fields.String(required=False),
})

daily_model = daily_without_id_model.clone('Daily', full_time_util, {
    'id': fields.Integer(readOnly=True),
})

daily_pagination_model = pagination_base_model.clone('dailyPagination', {
    'items': fields.List(fields.Nested(daily_model))
})

ns.add_model(daily_without_id_model.name, daily_without_id_model)
ns.add_model(daily_model.name, daily_model)
ns.add_model(daily_pagination_model.name, daily_pagination_model)

daily_list_args = reqparse.RequestParser()
daily_list_args.add_argument('page', type=int, location='args', required=True, help='Current page number.')
daily_list_args.add_argument('per_page', type=int, location='args', required=True, help='The number of items in a page.')
daily_list_args.add_argument('name',location='args')
daily_list_args.add_argument('system_type', location='args')
daily_list_args.add_argument('target_ip', location='args')
daily_list_args.add_argument('result', location='args')
daily_list_args.add_argument('execution_id', location='args')
daily_list_args.add_argument('start_time', location='args')
daily_list_args.add_argument('end_time', location='args')

daily_execution_record_list = reqparse.RequestParser()
daily_execution_record_list.add_argument('page', type=int, location='args', required=True, help='Current page number.')
daily_execution_record_list.add_argument('per_page', type=int, location='args', required=True, help='The number of items in a page.')
daily_execution_record_list.add_argument('name', location='args')
daily_execution_record_list.add_argument('system_type', location='args')
daily_execution_record_list.add_argument('creator', location='args')

@ns.route('/job-record/')
class dailys(Resource):
    """
    Shows a list of all inspection daily, and lets you POST to add new daily inspection
    """

    @ns.doc('list_all_daily_inspection')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'daily inspection list not found')
    @ns.expect(daily_list_args)
    @ns.marshal_list_with(job_record_pagination_model)
    def get(self):
        """
        list all daily inspection
        Returns:
            all daily inspection
        """
        args = daily_list_args.parse_args()
        page = args.page
        per_page = args.per_page
        name = args.name
        system_type = args.system_type
        target_ip = args.target_ip
        result = args.result
        execution_id = args.execution_id
        start_time = args.start_time
        end_time = args.end_time

        current_app.logger.debug("Get daily inspection list's params are: {}".format(args))
        try:
            daily_inspection = get_daily_host_result_list(page, per_page, name=name, system_type=system_type,
                                                          target_ip=target_ip, result=result,
                                                          execution_id=execution_id, start_time=start_time,
                                                          end_time=end_time)
            current_app.logger.info("Get daily inspection list's result with page num {}, and length is {}"
                                    .format(daily_inspection['page'], len(daily_inspection)))
        except SchedulerError as e:
            current_app.logger.error("instant daily list can\'t be found with params: page={}, per_page={}"
                                     .format(page, per_page))
            abort(404, e.message)
        return daily_inspection

@ns.route('/execution-record/')
class DailyJobRecords(Resource):
    """
    Shows a list of all inspection daily execution record
    """
    @ns.doc('list_all_execution_record')
    @ns.response(404, 'execution record list not found')
    @ns.marshal_list_with(execution_record_pagination_model)
    @ns.expect(daily_execution_record_list)
    def get(self):
        """
        list all inspection daily record
        Returns:
            all inspection daily record
        """
        args = daily_execution_record_list.parse_args()
        page = args.page
        per_page = args.per_page
        name = args.name
        creator = args.creator
        system_type = args.system_type

        current_app.logger.debug("Get inspection record list's params are: {}".format(args))
        try:
            inspection_record = get_daily_job_result_list(page, per_page, name=name, creator=creator,
                                                          system_type=system_type)
            current_app.logger.info("Get inspection record list's result with page num {}, and length is {}"
                                    .format(inspection_record['page'], len(inspection_record)))
        except ResourcesNotFoundError as e:
            current_app.logger.error("inspection record list can\'t be found with params: page={}, per_page={}"
                                     .format(page, per_page))
            abort(404, e.message)
        return inspection_record
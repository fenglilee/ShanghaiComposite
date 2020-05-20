#!/usr/bin/env python
# -*- coding:utf-8 -*-

from flask import current_app
from flask_restplus import Namespace, Model, fields, reqparse, Resource, abort

from aops.applications.database.apis.job.instant_job import get_instant_jobs_list, create_instant_job, \
    get_instant_job_with_id, update_instant_job_with_id, delete_instant_job_with_ids, get_instant_creator, carry_out
from aops.applications.database.apis.job.job import get_jobs_list, create_job, delete_jobs_with_ids, \
    start_or_stop_jobs, get_job_with_id, update_job_with_id, get_job_creator, get_job_with_enable
from aops.applications.database.apis.job.job_record import get_execution_record_list, \
    get_job_record_list, get_job_record_creator, execution_again, get_execution_record_creator, \
    stop_job_by_execution_id, get_job_execution_log
from aops.applications.database.apis.job.timed_job import get_timed_jobs_list, create_timed_job, \
    delete_timed_job_with_ids, get_timed_job_with_id, update_timed_job_with_id, get_timed_creator, enable_timed_jobs, \
    disable_periodic_jobs
from aops.applications.exceptions.exception import ResourcesNotFoundError, ResourceNotFoundError, \
    ResourceAlreadyExistError, SchedulerError, NoTaskError, NoPermissionError, ResourcesNotDisabledError, ConflictError, \
    ValidationError
from aops.applications.handlers.v1 import passport_auth
from aops.applications.handlers.v1.common import full_time_util, pagination_base_model

ns = Namespace('/v1/jobs', description='Jobs operations')

"""job"""
job_without_id_model = Model('JobWithoutID', {
    'name': fields.String(required=True, description='The job\'s name'),
    'description': fields.String(required=True, description='The job\'s description'),
    'system_type': fields.String(required=True, description='The job\'s system type'),
    'target_ip': fields.String,
    'status': fields.Boolean(required=True, default=0, description='Is this job enabled'),
    'execution_account': fields.String(required=True, description='The job\'s execution account'),
    'scheduling': fields.String(required=True, description='The job\'s scheduling'),
    'frequency': fields.Integer(required=True, description='The job\'s frequency'),
    'job_type': fields.String(required=True, description='The job\'s type'),
    'applications': fields.String(required=False, description='The job\'s applications'),
    'task_id_list': fields.String,
})

job_model = job_without_id_model.clone('Job', full_time_util, {
    'id': fields.Integer(readOnly=True, description='The job\'s identifier'),
    'creator': fields.String(required=True, description='The job\'s creator'),
    'success_rate': fields.Integer(required=False, default=0, description='The job\'s success rate'),
    'risk_level': fields.Integer(required=True, description='The job\'s risk level'),
    'business_group': fields.String(required=True),
})

job_update_model = job_without_id_model.clone('JobUpdate', {
    'creator': fields.String(required=True, description='The job\'s creator'),
    'success_rate': fields.Integer(required=False, default=0, description='The job\'s success rate'),
    'risk_level': fields.Integer(required=True, description='The job\'s risk level'),
})

job_pagination_model = pagination_base_model.clone('JobPagination', {
    'items': fields.List(fields.Nested(job_model))
})

job_ids_model = Model('JobIds', {
    'job_ids': fields.List(fields.String, description='Multiple id of jobs')
})

job_ids_operate_model = job_ids_model.clone('JobIdsOperate', {
    'status': fields.Boolean(required=True, description='Is this job enabled')
})

creator_model = Model('JobCreator', {
    'creator': fields.List(fields.String)
})

ns.add_model(job_without_id_model.name, job_without_id_model)
ns.add_model(job_model.name, job_model)
ns.add_model(job_pagination_model.name, job_pagination_model)
ns.add_model(job_ids_model.name, job_ids_model)
ns.add_model(job_ids_operate_model.name, job_ids_operate_model)
ns.add_model(job_update_model.name, job_update_model)
ns.add_model(creator_model.name, creator_model)

job_without_id_parser = reqparse.RequestParser()
job_without_id_parser.add_argument('name', type=unicode)
job_without_id_parser.add_argument('description', type=unicode)
job_without_id_parser.add_argument('system_type', type=unicode)
job_without_id_parser.add_argument('target_ip', type=list, location='json')
job_without_id_parser.add_argument('status', type=bool)
job_without_id_parser.add_argument('execution_account')
job_without_id_parser.add_argument('scheduling')
job_without_id_parser.add_argument('frequency', type=int)
job_without_id_parser.add_argument('job_type')
job_without_id_parser.add_argument('applications', type=unicode)
job_without_id_parser.add_argument('creator', type=unicode)
job_without_id_parser.add_argument('success_rate', type=int)
job_without_id_parser.add_argument('risk_level', type=int)
job_without_id_parser.add_argument('task_id_list', type=list, location='json')

job_parser = job_without_id_parser.copy()
job_parser.add_argument('id', type=int)

job_update_parser = job_without_id_parser.copy()
job_update_parser.add_argument('creator')
job_update_parser.add_argument('success_rate')
job_update_parser.add_argument('risk_level')

job_ids_parser = reqparse.RequestParser()
job_ids_parser.add_argument('job_ids', type=list, location='json')

job_ids_operate_parser = job_ids_parser.copy()
job_ids_operate_parser.add_argument('status', type=bool)

job_list_args = reqparse.RequestParser()
job_list_args.add_argument('page', type=int, location='args', required=True, help='Current page number.')
job_list_args.add_argument('per_page', type=int, location='args', required=True, help='The number of items in a page.')
job_list_args.add_argument('name', location='args')
job_list_args.add_argument('job_type', location='args', choices=('ordinary', 'update', 'quit', 'inspection', ''))
job_list_args.add_argument('system_type', location='args', choices=('linux', 'windows', ''))
job_list_args.add_argument('creator', location='args')
job_list_args.add_argument('start_time', location='args')
job_list_args.add_argument('end_time', location='args')
job_list_args.add_argument('fq', location='args', dest="fuzzy_query")
"""end job"""

"""instant job"""
instant_job_model = full_time_util.clone('InstantJob', {
    'id': fields.Integer(readOnly=True, description='The instant job\'s identifier'),
    'execution_id': fields.String(required=False, description='The instant job\'s execution id'),
    'result': fields.String(required=True, default=0, description='Is this instant job result'),
    'start_time': fields.DateTime(required=False),
    'end_time': fields.DateTime(required=False),
    'executive': fields.String(required=False, description='The instant job\'s executive'),

    'name': fields.String(required=True, description='The instant job\'s name'),
    'status': fields.String(required=True, default=0, description='Is this instant job status'),
    'job_type': fields.String(required=True, description='The instant job\'s type'),
    'creator': fields.String(required=True),
    'execution_account': fields.String(required=True, description='The instant job\'s execution account'),
    'execution_type': fields.String(required=True),
    'business_group': fields.String(required=True),
    'target_ip': fields.String(required=True, description='The instant job\'s target ip'),
    'frequency': fields.Integer(required=True, description='The instant job\'s frequency'),
    'description': fields.String(required=True, description='The instant job\'s description'),
    'system_type': fields.String(required=True, description='The instant job\'s system type'),
    'scheduling': fields.String(required=True, description='The instant job\'s scheduling'),
    'applications': fields.String(required=False, description='The instant job\'s applications'),
    'success_rate': fields.Integer(required=False, default=0, description='The job\'s success rate'),
    'risk_level': fields.Integer(required=True, description='The job\'s risk level'),
})

instant_job_pagination_model = pagination_base_model.clone('InstantJobPagination', {
    'items': fields.List(fields.Nested(instant_job_model))
})

job_id_model = Model('JobID', {
    'job_id': fields.Integer(required=True),
})

instant_job_update_model = Model('InstantJobUpdate', {
    'execution_account': fields.String(required=False, description='The instant job\'s execution account'),
    'target_ip': fields.String(required=False, description='The instant job\'s target ip'),
    'frequency': fields.Integer(required=False, description='The instant job\'s frequency'),
    'scheduling': fields.String(required=False, description='The instant job\'s scheduling'),
})

instant_model = Model('Instant', {
    'job_info': fields.String(required=True)
})

carry_out_model = Model('CarryOut', {
    'execution_id': fields.String(required=False),
})

ns.add_model(instant_job_model.name, instant_job_model)
ns.add_model(instant_job_pagination_model.name, instant_job_pagination_model)
ns.add_model(job_id_model.name, job_id_model)
ns.add_model(instant_job_update_model.name, instant_job_update_model)
ns.add_model(instant_model.name, instant_model)
ns.add_model(carry_out_model.name, carry_out_model)

job_id_parser = reqparse.RequestParser()
job_id_parser.add_argument('job_id', type=int)

instant_parser = reqparse.RequestParser()
instant_parser.add_argument('job_info')

carry_out_parser = reqparse.RequestParser()
carry_out_parser.add_argument('execution_id')

instant_job_update_parser = reqparse.RequestParser()
instant_job_update_parser.add_argument('execution_account')
instant_job_update_parser.add_argument('target_ip', type=list, location='json')
instant_job_update_parser.add_argument('frequency', type=int)
instant_job_update_parser.add_argument('scheduling')

instant_job_list_args = reqparse.RequestParser()
instant_job_list_args.add_argument('page', type=int, location='args', required=True, help='Current page number.')
instant_job_list_args.add_argument('per_page', type=int, location='args', required=True,
                                   help='The number of items in a page.')

"""end instant job"""

"""timed job"""
timed_job_without_id_model = Model('TimedJobWithoutID', {
    'name': fields.String(required=True),
    'execution_account': fields.String(required=True),
    'target_ip': fields.String(required=True),
    'frequency': fields.Integer(required=True),
    'description': fields.String(required=True),
    'timed_type': fields.String(required=True),
    'timed_expression': fields.String(required=False),
    'timed_date': fields.String(required=False),
    'status': fields.Integer(required=True),
    'timed_config': fields.String(required=True),
    'job_id': fields.Integer,

})

timed_job_model = timed_job_without_id_model.clone('TimedJob', full_time_util, {
    'id': fields.Integer(readOnly=True),
    'creator': fields.String(required=True),
    'success_rate': fields.Integer(required=False, default=0),
    'risk_level': fields.Integer(required=True),
    'job_type': fields.String(required=True, description='The instant job\'s type'),
    'system_type': fields.String(required=True, description='The instant job\'s system type'),
    'scheduling': fields.String(required=True, description='The instant job\'s scheduling'),
    'applications': fields.String(required=False, description='The instant job\'s applications'),
    'executions_num': fields.Integer,
    'execution_type': fields.String(),
    'execution_id': fields.String(),
    'business_group': fields.String(),
    'last_time': fields.DateTime,
    'result': fields.String(required=True, default=0, description='Is this instant job result'),

})

timed_job_pagination_model = pagination_base_model.clone('TimedJobPagination', {
    'items': fields.List(fields.Nested(timed_job_model))
})

timed_job_update_model = Model('TimedJobUpdate', {
    'execution_account': fields.String(required=False, description='The instant job\'s execution account'),
    'target_ip': fields.String(required=False, description='The instant job\'s target ip'),
    'frequency': fields.Integer(required=False, description='The instant job\'s frequency'),
    'description': fields.String(required=False, description='The instant job\'s description'),
    'timed_config': fields.String(required=False),
    'timed_expression': fields.String(required=False),
    'timed_date': fields.String(required=False),
    'timed_type': fields.String(required=False),
    'scheduling': fields.String(required=False, description='The instant job\'s scheduling'),
})

disable_job_model = Model('DisableJob', {
    'id': fields.Integer(required=True),
    'execution_id': fields.String(required=True)
})

ns.add_model(timed_job_without_id_model.name, timed_job_without_id_model)
ns.add_model(timed_job_model.name, timed_job_model)
ns.add_model(timed_job_pagination_model.name, timed_job_pagination_model)
ns.add_model(timed_job_update_model.name, timed_job_update_model)
ns.add_model(disable_job_model.name, disable_job_model)

job_info_parser = reqparse.RequestParser()
job_info_parser.add_argument('job_info')

disable_job_parser = reqparse.RequestParser()
disable_job_parser.add_argument('execution_id')
disable_job_parser.add_argument('id', type=int)


timed_job_without_id_parser = reqparse.RequestParser()
timed_job_without_id_parser.add_argument('name')
timed_job_without_id_parser.add_argument('execution_account')
timed_job_without_id_parser.add_argument('target_ip', type=list, location='json')
timed_job_without_id_parser.add_argument('frequency', type=int)
timed_job_without_id_parser.add_argument('description')
timed_job_without_id_parser.add_argument('timed_type')
timed_job_without_id_parser.add_argument('timed_expression')
timed_job_without_id_parser.add_argument('timed_date')
timed_job_without_id_parser.add_argument('timed_config')
timed_job_without_id_parser.add_argument('status', type=int)
timed_job_without_id_parser.add_argument('job_id', type=int)

timed_job_list_args = reqparse.RequestParser()
timed_job_list_args.add_argument('page', type=int, location='args', required=True, help='Current page number.')
timed_job_list_args.add_argument('per_page', type=int, location='args', required=True,
                                 help='The number of items in a page.')
timed_job_list_args.add_argument('name', location='args')
timed_job_list_args.add_argument('system_type', location='args')
timed_job_list_args.add_argument('job_type', location='args')
timed_job_list_args.add_argument('target_ip')
timed_job_list_args.add_argument('creator', location='args')
timed_job_list_args.add_argument('start_time', location='args')
timed_job_list_args.add_argument('end_time', location='args')
timed_job_list_args.add_argument('fq', location='args', dest="fuzzy_query")

timed_job_update_parser = reqparse.RequestParser()
timed_job_update_parser.add_argument('execution_account')
timed_job_update_parser.add_argument('target_ip', type=list, location='json')
timed_job_update_parser.add_argument('frequency', type=int)
timed_job_update_parser.add_argument('description')
timed_job_update_parser.add_argument('timed_config')
timed_job_update_parser.add_argument('timed_expression')
timed_job_update_parser.add_argument('timed_date')
timed_job_update_parser.add_argument('timed_type')
timed_job_update_parser.add_argument('scheduling')

"""end timed job"""

""" execution record"""
execution_record_without_id_model = Model('ExecutionRecordWithoutID', {
    'job_info': fields.String(required=True),
    'execution_uuid': fields.String(required=True),
})

execution_record_model = full_time_util.clone('ExecutionRecord', {
    'id': fields.Integer(readOnly=True),
    'execution_id': fields.String(required=False),
    'creator': fields.String(required=True),
    'name': fields.String(required=True),
    'job_type': fields.String(required=True),
    'system_type': fields.String(required=True),
    'target_ip': fields.String(required=True),
    'time': fields.Float(required=True),
    'end_time': fields.DateTime(required=False),
    'status': fields.String(required=True),
    'result': fields.String(required=True),
    'execution_type': fields.String(required=True),
    'business_group': fields.String(required=True),
    'execution_account': fields.String(required=False),
    'frequency': fields.Integer(required=False),
    'scheduling': fields.String(required=False),
    'applications': fields.String(required=False),
})

execution_record_pagination_model = pagination_base_model.clone('ExecutionRecordPagination', {
    'items': fields.List(fields.Nested(execution_record_model))
})

ns.add_model(execution_record_without_id_model.name, execution_record_without_id_model)
ns.add_model(execution_record_model.name, execution_record_model)
ns.add_model(execution_record_pagination_model.name, execution_record_pagination_model)

execution_record_without_id_parser = reqparse.RequestParser()
execution_record_without_id_parser.add_argument('job_info', location='json')
execution_record_without_id_parser.add_argument('execution_uuid', location='json')

get_execution_creator_parser = reqparse.RequestParser()
get_execution_creator_parser.add_argument('execution_type', location='args')

execution_record_list_args = reqparse.RequestParser()
execution_record_list_args.add_argument('page', type=int, location='args', required=True, help='Current page number.')
execution_record_list_args.add_argument('per_page', type=int, location='args', required=True,
                                        help='The number of items in a page.')
execution_record_list_args.add_argument('name', location='args')
execution_record_list_args.add_argument('system_type', location='args')
execution_record_list_args.add_argument('job_type', location='args')
execution_record_list_args.add_argument('target_ip', location='args')
execution_record_list_args.add_argument('creator', location='args')
execution_record_list_args.add_argument('start_time', location='args')
execution_record_list_args.add_argument('end_time', location='args')
execution_record_list_args.add_argument('execution_type', location='args')
execution_record_list_args.add_argument('fq', location='args', dest="fuzzy_query")

""" end execution record"""

"""job record"""
job_record_model = full_time_util.clone('JobRecord', {
    'id': fields.Integer(readOnly=True),
    'creator': fields.String(required=True),
    'description': fields.String,
    'execution_id': fields.String(required=False),
    'execution_type': fields.String(required=True),
    'name': fields.String(required=True),
    'job_type': fields.String(required=True),
    'system_type': fields.String(required=True),
    'target_ip': fields.String(required=True),
    'start_time': fields.String(required=False),
    'end_time': fields.String(required=False),
    'status': fields.String(required=True),
    'result': fields.String(required=True),
    'time': fields.String(required=True),
    'business_group': fields.String(required=True),
    'scheduling': fields.String
})

job_record_pagination_model = pagination_base_model.clone('JobRecordPagination', {
    'items': fields.List(fields.Nested(job_record_model))
})

get_execution_log_model = Model('GetExecutionLog', {
    'execution_id': fields.String(required=True),
    'target_ip': fields.String(required=True),
})

execution_log_result_model = Model('ExecutionLogResult', {
    'execution_log': fields.String(required=True)
})

ns.add_model(job_record_model.name, job_record_model)
ns.add_model(job_record_pagination_model.name, job_record_pagination_model)
ns.add_model(get_execution_log_model.name, get_execution_log_model)
ns.add_model(execution_log_result_model.name, execution_log_result_model)

get_execution_log_parser = reqparse.RequestParser()
get_execution_log_parser.add_argument('execution_id', location='args')
get_execution_log_parser.add_argument('target_ip', location='args')

job_record_list_args = reqparse.RequestParser()
job_record_list_args.add_argument('page', type=int, location='args', required=True, help='Current page number.')
job_record_list_args.add_argument('per_page', type=int, location='args', required=True,
                                  help='The number of items in a page.')
job_record_list_args.add_argument('id', location='args')
job_record_list_args.add_argument('name', location='args')
job_record_list_args.add_argument('creator', location='args')
job_record_list_args.add_argument('system_type', location='args')
job_record_list_args.add_argument('job_type', location='args')
job_record_list_args.add_argument('target_ip', location='args')
job_record_list_args.add_argument('execution_id', location='args')
job_record_list_args.add_argument('start_time', location='args')
job_record_list_args.add_argument('end_time', location='args')
job_record_list_args.add_argument('execution_type', location='args')
job_record_list_args.add_argument('fq', location='args', dest="fuzzy_query")
"""end job record"""


@ns.route('/')
class Jobs(Resource):
    """
    Shows a list of all jobs, and lets you POST to add new jobs
    """

    @ns.doc('list_all_jobs')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'Job list not found')
    @ns.marshal_list_with(job_pagination_model)
    @ns.expect(job_list_args)
    def get(self):
        """
        list all jobs
        Returns:
            all jobs
        """
        args = job_list_args.parse_args()
        page = args.page
        per_page = args.per_page
        name = args.name
        job_type = args.job_type
        creator = args.creator
        start_time = args.start_time
        end_time = args.end_time
        system_type = args.system_type
        fuzzy_query = args.fuzzy_query
        current_app.logger.debug("Get job list's params are: {}".format(args))
        try:
            jobs = get_jobs_list(page, per_page, name=name, job_type=job_type, creator=creator, start_time=start_time,
                                 system_type=system_type, end_time=end_time, fuzzy_query=fuzzy_query)
            current_app.logger.info(
                "Get job list's result with page num {}, and length is {}".format(jobs.page, len(jobs.items)))
        except ResourcesNotFoundError as e:
            current_app.logger.error(
                "Jobs list can\'t be found with params: page={}, per_page={}".format(page, per_page))
            abort(404, e.message)
        return jobs

    @ns.doc('create_job')
    @ns.expect(job_without_id_model)
    @ns.marshal_with(job_model, code=200)
    def post(self):
        """
        create a job items
        Returns:
            the new job items
        """
        args = job_parser.parse_args()
        current_app.logger.debug("Create job item's params are: {}".format(args))
        try:
            created_job = create_job(args)
        except NoTaskError as e:
            abort(404, e.message)
        except ResourceAlreadyExistError as e:
            current_app.logger.error("{} this job name already exists".format(args.name))
            abort(409, e.message)
        current_app.logger.info("Created job item's result is: {}".format(created_job))
        return created_job

    @ns.doc('delete_jobs')
    @ns.expect(job_ids_model)
    @ns.marshal_with(job_model, code=201)
    def delete(self):
        """
        Delete multiple jobs
        Returns:
            The deleted jobs
        """
        args = job_ids_parser.parse_args()
        current_app.logger.debug("Delete job item with job ids: {}".format(args.job_ids))
        try:
            result = delete_jobs_with_ids(args)
        except ResourceNotFoundError as e:
            current_app.logger.error('job not found')
            abort(404, e.message)
        except ResourcesNotDisabledError as e:
            current_app.logger.error('This job no stop')
            abort(409, e.message)
        return result

    @ns.doc('start_or_stop_jobs')
    @ns.expect(job_ids_operate_model)
    @ns.marshal_with(job_model, code=201)
    def put(self):
        """
        Start or stop multiple jobs
        Returns:
           The Operational job
        """
        args = job_ids_operate_parser.parse_args()
        current_app.logger.debug("Put job item with job ids: {}".format(args.job_ids))
        try:
            result = start_or_stop_jobs(args)
        except ResourceNotFoundError as e:
            current_app.logger.error('job not found')
            abort(404, e.message)
        except ConflictError as e:
            current_app.logger.error('This job is used by other')
            abort(404, e.message)
        current_app.logger.info("Put job item with job ids {},and latest info is: {}"
                                .format(args.job_ids, [job.to_dict() for job in result]))
        return result


@ns.route('/<int:identifier>')
@ns.response(404, 'Job not found')
@ns.param('identifier', 'The Job\'s identifier')
class Job(Resource):
    """Show a single job item and lets you delete them"""

    @ns.doc('get_job')
    @ns.marshal_with(job_model)
    @ns.response(200, 'Get single job item', model=job_model)
    def get(self, identifier):
        """
        Fetch a given job with identifier.
        Args:
            identifier: job id

        Returns:
            Get the job item with id.
        """
        current_app.logger.debug("Get job item with id: {}".format(identifier))
        try:
            job = get_job_with_id(identifier)
            current_app.logger.info("Get job item with id {} 's result is: {}".format(identifier, job.to_dict()))
        except ResourceNotFoundError as e:
            current_app.logger.error("job item can\'t be found with id {}".format(identifier))
            abort(404, e.message)
        return job

    @ns.expect(job_update_model)
    @ns.response(200, 'job updated')
    @ns.marshal_with(job_model)
    def put(self, identifier):
        """Update a job given its identifier"""

        job_info = job_update_parser.parse_args()
        current_app.logger.debug("Update job item's params are: {}".format(job_info))
        try:
            result = update_job_with_id(identifier, job_info)
        except NoTaskError as e:
            abort(404, e.message)
        except ResourcesNotFoundError as e:
            current_app.logger.error("job item can\'t be found with id {}".format(identifier))
            abort(404, e.message)
        except NoPermissionError as e:
            current_app.logger.error("no permission to change this job {}".format(identifier))
            abort(404, e.message)
        except ResourcesNotDisabledError as e:
            current_app.logger.error('This job no stop')
            abort(404, e.message)
        current_app.logger.info("Update job item's result is: {}".format(result))
        return result, 200


@ns.route('/job-creator/')
class JobCreator(Resource):
    """
    Screening job
    """

    @ns.doc('list_creator')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'creator list not found')
    @ns.marshal_list_with(creator_model)
    def get(self):
        """Get all creator"""
        try:
            creator = get_job_creator()
            current_app.logger.info("Get creator list's result with {}".format(creator))
        except ResourcesNotFoundError as e:
            current_app.logger.error("creator list can\'t be found ")
            abort(404, e.message)
        return creator


@ns.route('/enable/')
class EnableJobs(Resource):
    """
    Shows a list of all jobs, and lets you POST to add new jobs
    """
    @ns.doc('list_all_enble_jobs')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'Enable job list not found')
    @ns.marshal_list_with(job_pagination_model)
    @ns.expect(job_list_args)
    def get(self):
        """
        list all jobs
        Returns:
            all jobs
        """
        args = job_list_args.parse_args()
        page = args.page
        per_page = args.per_page
        system_type = args.system_type
        fuzzy_query = args.fuzzy_query

        current_app.logger.debug("Get enable job list's params are: {}".format(args))
        try:
            jobs = get_job_with_enable(page, per_page, system_type, fuzzy_query)
            current_app.logger.info(
                "Get enable job list's result with page num {}, and length is {}".format(jobs.page, len(jobs.items)))
        except ResourcesNotFoundError as e:
            current_app.logger.error(
                "Enable jobs list can\'t be found with params: page={}, per_page={}".format(page, per_page))
            abort(404, e.message)
        return jobs

"""
 instant job
"""


@ns.route('/instant/')
class InstantJobs(Resource):
    """
    Shows a list of all instant jobs, and lets you POST to add new instant jobs
    """

    @ns.doc('list_all_instant_jobs')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'Instant Job list not found')
    @ns.marshal_list_with(instant_job_pagination_model)
    @ns.expect(instant_job_list_args)
    def get(self):
        """
        list all instant jobs
        Returns:
            all instant jobs
        """
        args = instant_job_list_args.parse_args()
        page = args.page
        per_page = args.per_page
        current_app.logger.debug("Get instant job list's params are: {}".format(args))
        try:
            instant_jobs = get_instant_jobs_list(page, per_page)
            current_app.logger.info("Get instant job list's result with page num {}, and length is {}"
                                    .format(instant_jobs.page, len(instant_jobs.items)))
        except ResourcesNotFoundError as e:
            current_app.logger.error(
                "Instant Jobs list can\'t be found with params: page={}, per_page={}".format(page, per_page))
            abort(404, e.message)
        return instant_jobs

    @ns.doc('create_instant_job')
    @ns.expect(job_id_model)
    @ns.marshal_with(instant_job_model, code=201)
    @passport_auth()
    def post(self):
        """
        create a instant job items
        Returns:
            the new instant job items
        """
        args = job_id_parser.parse_args()
        current_app.logger.debug("Create instant job item's params are: {}".format(args))
        try:
            created_instant_job = create_instant_job(args)
        except ResourceAlreadyExistError as e:
            current_app.logger.error(e.message)
            abort(409, e.message)
        current_app.logger.info("Created instant job item's result is: {}".format(created_instant_job))
        return created_instant_job, 201

    @ns.doc('delete_instant_jobs')
    @ns.expect(job_ids_model)
    @ns.marshal_with(instant_job_model, code=200)
    @passport_auth()
    def delete(self):
        """
        Delete multiple instant jobs
        Returns:
            The deleted jobs
        """
        args = job_ids_parser.parse_args()
        current_app.logger.debug("Delete instant job item with job ids: {}".format(args.job_ids))
        try:
            result = delete_instant_job_with_ids(args)
        except ResourceAlreadyExistError as e:
            current_app.logger.error(e.message)
            abort(409, e.message)
        current_app.logger.info("Delete instant job item's result is: {}".format(result))
        return result


@ns.route('/instant/<int:identifier>')
@ns.response(404, 'Instant Job not found')
@ns.param('identifier', 'The instant Job\'s identifier')
class InstantJob(Resource):
    """Show a single instant job item and lets you delete them"""

    @ns.doc('get_instant_job')
    @ns.marshal_with(instant_job_model)
    @ns.response(200, 'Get single instant job item', model=instant_job_model)
    def get(self, identifier):
        """
        Fetch a given instant job with identifier.
        Args:
            identifier: instant job id

        Returns:
            Get the instant job item with id.
        """
        current_app.logger.debug("Get instant job item with id: {}".format(identifier))
        try:
            instant_job = get_instant_job_with_id(identifier)
            current_app.logger.info("Get instant job item with id {} 's result is: {}"
                                    .format(identifier, instant_job.to_dict()))
        except ResourceNotFoundError as e:
            current_app.logger.error("instant job item can\'t be found with id {}".format(identifier))
            abort(404, e.message)
        return instant_job

    @ns.expect(instant_job_update_model)
    @ns.response(200, 'job updated')
    @ns.marshal_with(instant_job_model)
    def put(self, identifier):
        """Update a instant job given its identifier"""
        job_info = instant_job_update_parser.parse_args()
        execution_account = job_info.execution_account
        target_ip = job_info.target_ip
        frequency = job_info.frequency
        scheduling = job_info.scheduling

        current_app.logger.debug("Update instant job item's params are: {}".format(job_info))
        try:
            result = update_instant_job_with_id(identifier, execution_account=execution_account, target_ip=target_ip,
                                            frequency=frequency, scheduling=scheduling)
        except ResourceNotFoundError as e:
            current_app.logger.error("instant job item can\'t be found with id {}".format(identifier))
            abort(404, e.message)
        current_app.logger.info("Update instant job item's result is: {}".format(result))
        return result, 200


@ns.route('/instant/creator/')
class InstantJobCreator(Resource):
    """
    Screening job
    """

    @ns.doc('list_creator')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'creator list not found')
    @ns.marshal_list_with(creator_model)
    def get(self):
        """Get all creator"""
        try:
            creator = get_instant_creator()
            current_app.logger.info("Get creator list's result with {}".format(creator))
        except ResourcesNotFoundError as e:
            current_app.logger.error("creator list can\'t be found ")
            abort(404, e.message)
        return creator


@ns.route('/instant/carry-out')
class CarryOut(Resource):
    """
    carry out instant job
    """

    @ns.doc('carry_out')
    @ns.expect(instant_model)
    @ns.marshal_list_with(carry_out_model)
    @passport_auth()
    def post(self):
        """carry out instant job"""
        args = instant_parser.parse_args()
        current_app.logger.debug("carry out instant job item's params are: {}".format(args))
        try:
            result = carry_out(args.job_info)
        except SchedulerError as e:
            current_app.logger.error(e.message)
            abort(409, e.message)
        except ValidationError as e:
            current_app.logger.error(e.message)
            abort(404, e.message)
        current_app.logger.info("carry out instant job item's result is: {}".format(result))
        return result


@ns.route('/carry-out/again/')
class CarryOutAgain(Resource):
    """
    carry out job again
    """

    @ns.doc('carry_out_again')
    @ns.expect(carry_out_model)
    @ns.marshal_list_with(carry_out_model)
    def post(self):
        """carry out job again"""
        args = carry_out_parser.parse_args()
        current_app.logger.debug("carry out job again item's params are: {}".format(args))
        try:
            result = execution_again(args.execution_id)
        except SchedulerError as e:
            current_app.logger.error(e.message)
            abort(409, e.message)
        current_app.logger.info("carry out job again item's result is: {}".format(result))
        return result


@ns.route('/<string:execution_id>/stop/')
class StopInstantJob(Resource):
    """
    stop a job
    """

    @ns.doc('stop_instant_job')
    @ns.marshal_list_with(carry_out_model)
    def post(self, execution_id):
        """stop_instant_job"""
        try:
            result = stop_job_by_execution_id(execution_id)
        except ResourceAlreadyExistError as e:
            current_app.logger.error(e.message)
            abort(409, e.message)
        current_app.logger.info("stop instant job item's result is: {}".format(result))
        return result


"""
 timed job
"""


@ns.route('/timed/')
class TimedJobs(Resource):
    """
    Shows a list of all timed jobs, and lets you POST to add new timed jobs
    """

    @ns.doc('list_all_timed_jobs')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'Timed Job list not found')
    @ns.marshal_list_with(timed_job_pagination_model)
    @ns.expect(timed_job_list_args)
    def get(self):
        """
        list all timed jobs
        Returns:
            all timed jobs
        """
        args = timed_job_list_args.parse_args()
        page = args.page
        per_page = args.per_page
        name = args.name
        system_type = args.system_type
        job_type = args.job_type
        target_ip = args.target_ip
        creator = args.creator
        start_time = args.start_time
        end_time = args.end_time
        fuzzy_query = args.fuzzy_query
        current_app.logger.debug("Get timed job list's params are: {}".format(args))
        try:
            timed_jobs = get_timed_jobs_list(page, per_page, name=name, system_type=system_type, job_type=job_type,
                                             target_ip=target_ip, creator=creator, start_time=start_time,
                                             end_time=end_time, fuzzy_query=fuzzy_query)
            current_app.logger.info("Get timed job list's result with page num {}, and length is {}"
                                    .format(timed_jobs.page, len(timed_jobs.items)))
        except ResourcesNotFoundError as e:
            current_app.logger.error("timed Jobs list can\'t be found with params: page={}, per_page={}"
                                     .format(page, per_page))
            abort(404, e.message)
        return timed_jobs

    @ns.doc('create_timed_job')
    @ns.expect(timed_job_without_id_model)
    @ns.marshal_with(timed_job_model, code=200)
    def post(self):
        """
        create a timed job items
        Returns:
            the new timed job items
        """
        args = timed_job_without_id_parser.parse_args()
        current_app.logger.debug("Create timed job item's params are: {}".format(args))
        try:
            created_timed_job = create_timed_job(args)
        except ResourceAlreadyExistError as e:
            current_app.logger.error("{} this job name already exists".format(args.name))
            abort(404, e.message)
        current_app.logger.info("Created timed job item's result is: {}".format(created_timed_job))
        return created_timed_job

    @ns.doc('delete_timed_jobs')
    @ns.expect(job_ids_model)
    @ns.marshal_with(timed_job_model, code=200)
    def delete(self):
        """
        Delete multiple timed jobs
        Returns:
            The deleted jobs
        """
        args = job_ids_parser.parse_args()
        current_app.logger.debug("Delete timed job item with job ids: {}".format(args.job_ids))
        try:
            result = delete_timed_job_with_ids(args)
        except ResourceNotFoundError as e:
            current_app.logger.error('job not found')
            abort(404, e.message)
        except ResourcesNotDisabledError as e:
            current_app.logger.error('This job no stop')
            abort(409, e.message)
        return result, 200


@ns.route('/timed/<int:identifier>')
@ns.response(404, 'timed Job not found')
@ns.param('identifier', 'The timed Job\'s identifier')
class TimedJob(Resource):
    """Show a single timed job item and lets you delete them"""

    @ns.doc('get_timed_job')
    @ns.marshal_with(timed_job_model)
    @ns.response(200, 'Get single instant job item', model=timed_job_model)
    @passport_auth()
    def get(self, identifier):
        """
        Fetch a given timed job with identifier.
        Args:
            identifier: timed job id

        Returns:
            Get the timed job item with id.
        """
        current_app.logger.debug("Get timed job item with id: {}".format(identifier))
        try:
            timed_job = get_timed_job_with_id(identifier)
            current_app.logger.info("Get timed job item with id {} 's result is: {}"
                                    .format(identifier, timed_job.to_dict()))
        except ResourceNotFoundError as e:
            current_app.logger.error("timed job item can\'t be found with id {}".format(identifier))
            abort(404, e.message)
        return timed_job

    @ns.expect(timed_job_update_model)
    @ns.response(200, 'timed job updated')
    @ns.marshal_with(timed_job_model)
    def put(self, identifier):
        """Update a timed job given its identifier"""
        job_info = timed_job_update_parser.parse_args()
        execution_account = job_info.execution_account
        target_ip = job_info.target_ip
        frequency = job_info.frequency
        scheduling = job_info.scheduling
        description = job_info.description
        timed_config = job_info.timed_config
        timed_expression = job_info.timed_expression
        timed_date = job_info.timed_date
        timed_type = job_info.timed_type

        current_app.logger.debug("Update timed job item's params are: {}".format(job_info))
        try:
            result = update_timed_job_with_id(identifier, execution_account=execution_account, target_ip=target_ip,
                                              frequency=frequency, scheduling=scheduling, description=description,
                                              timed_config=timed_config, timed_expression=timed_expression,
                                              timed_date=timed_date, timed_type=timed_type)
        except ResourceNotFoundError as e:
            current_app.logger.error("timed job item can\'t be found with id {}".format(identifier))
            abort(404, e.message)
        current_app.logger.info("Update timed job item's result is: {}".format(result))
        return result, 200


@ns.route('/timed/creator/')
class TimedJobCreator(Resource):
    """
    Screening job
    """

    @ns.doc('list_creator')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'creator list not found')
    @ns.marshal_list_with(creator_model)
    def get(self):
        """Get all creator"""
        try:
            creator = get_timed_creator()
            current_app.logger.info("Get creator list's result with {}".format(creator))
        except ResourcesNotFoundError as e:
            current_app.logger.error("creator list can\'t be found ")
            abort(404, e.message)
        return creator


@ns.route('/timed/enable/')
class TimedJobEnable(Resource):
    """
    Screening job
    """

    @ns.doc('enable_timed_jobs')
    @ns.expect(instant_model)
    def put(self):
        """

        Start multiple timed jobs
        Returns:
           The Operational job
        """
        args = job_info_parser.parse_args()
        current_app.logger.debug("Put job item with job ids")
        try:
            result = enable_timed_jobs(args.job_info)
        except ResourceAlreadyExistError as e:
            current_app.logger.error('This job is enable already')
            abort(404, e.message)
        except SchedulerError as e:
            current_app.logger.error('Scheduling module request not found')
            abort(404, e.message)
        return result


@ns.route('/timed/disable/')
class TimedJobDisabled(Resource):
    """
    Screening job
    """

    @ns.doc('disable_periodic_jobs')
    @ns.expect(disable_job_model)
    def put(self):
        """
        Returns:The Operational job
        """
        args = disable_job_parser.parse_args()
        current_app.logger.debug("Disable job item with job")
        try:
            result = disable_periodic_jobs(args.execution_id, args.id)
        except ResourceAlreadyExistError as e:
            current_app.logger.error('This job not enable')
            abort(404, e.message)
        except SchedulerError as e:
            current_app.logger.error('Scheduling module request not found')
            abort(404, e.message)
        return result


"""
 Execution Record
"""


@ns.route('/execution-record/')
class ExecutionRecords(Resource):
    """
    Shows a list of all execution record
    """

    @ns.doc('list_all_execution_record')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'execution record list not found')
    @ns.marshal_list_with(execution_record_pagination_model)
    @ns.expect(execution_record_list_args)
    def get(self):
        """
        list all execution record
        Returns:
            all execution record
        """
        args = execution_record_list_args.parse_args()
        page = args.page
        per_page = args.per_page
        name = args.name
        system_type = args.system_type
        job_type = args.job_type
        target_ip = args.target_ip
        creator = args.creator
        start_time = args.start_time
        end_time = args.end_time
        execution_type = args.execution_type
        fuzzy_query = args.fuzzy_query
        current_app.logger.debug("Get execution record list's params are: {}".format(args))
        try:
            execution_record = get_execution_record_list(page, per_page, name=name, system_type=system_type,
                                                         job_type=job_type, target_ip=target_ip, creator=creator,
                                                         start_time=start_time, end_time=end_time,
                                                         execution_type=execution_type,
                                                         fuzzy_query=fuzzy_query)
            current_app.logger.info("Get execution record list's result with page num {}, and length is {}"
                                    .format(execution_record['page'], len(execution_record['items'])))
        except SchedulerError as e:
            current_app.logger.error("execution record list can\'t be found with params: page={}, per_page={}"
                                     .format(page, per_page))
            abort(404, e.message)
        return execution_record


@ns.route('/execution-record/creator/')
class ExecutionRecordCreator(Resource):
    """
    Screening job
    """

    @ns.doc('list_creator')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'creator list not found')
    @ns.expect(get_execution_creator_parser)
    @ns.marshal_list_with(creator_model)
    def get(self):
        """Get all creator"""
        args = get_execution_creator_parser.parse_args()
        try:
            creator = get_execution_record_creator(execution_type=args.execution_type)
            current_app.logger.info("Get creator list's result with {}".format(creator))
        except SchedulerError as e:
            current_app.logger.error("creator list can\'t be found ")
            abort(404, e.message)
        return creator


"""
Job Record
"""


@ns.route('/job-record/')
class JobRecords(Resource):
    """
    Shows a list of all job record
    """

    @ns.doc('list_all_job_record')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'job record list not found')
    @ns.marshal_list_with(job_record_pagination_model)
    @ns.expect(job_record_list_args)
    @passport_auth()
    def get(self):
        """
        list all job record
        Returns:
            all job record
        """
        args = job_record_list_args.parse_args()
        page = args.page
        per_page = args.per_page
        id = args.id
        name = args.name
        creator = args.creator
        system_type = args.system_type
        job_type = args.job_type
        target_ip = args.target_ip
        execution_id = args.execution_id
        start_time = args.start_time
        end_time = args.end_time
        execution_type = args.execution_type
        fuzzy_query = args.fuzzy_query
        current_app.logger.debug("Get job record list's params are: {}".format(args))
        try:
            job_record = get_job_record_list(page, per_page, id=id, name=name, creator=creator, system_type=system_type,
                                             job_type=job_type, target_ip=target_ip, execution_id=execution_id,
                                             start_time=start_time, end_time=end_time, execution_type=execution_type,
                                             fuzzy_query=fuzzy_query)
            current_app.logger.info("Get job record list's result with page num {}, and length is {}"
                                    .format(job_record['page'], len(job_record['items'])))
        except SchedulerError as e:
            current_app.logger.error("job record list can\'t be found with params: page={}, per_page={}"
                                     .format(page, per_page))
            abort(404, e.message)
        return job_record


@ns.route('/job-record/creator/')
class JobRecordCreator(Resource):

    @ns.doc('list_creator')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'creator list not found')
    @ns.marshal_list_with(creator_model)
    def get(self):
        """Get all creator"""
        try:
            creator = get_job_record_creator()
            current_app.logger.info("Get creator list's result with {}".format(creator))
        except SchedulerError as e:
            current_app.logger.error("creator list can\'t be found ")
            abort(404, e.message)
        return creator


@ns.route('/job-record/log/')
class JobExecutionLog(Resource):

    @ns.doc('get_job_execution_log')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'not found')
    @ns.expect(get_execution_log_parser)
    @ns.marshal_with(execution_log_result_model)
    def get(self):
        """Get execution log"""
        args = get_execution_log_parser.parse_args()
        current_app.logger.debug("Get job execution log params are: {}".format(args))
        try:
            execution_log = get_job_execution_log(args)
            current_app.logger.info("Get execution log result with {}".format(execution_log))
        except SchedulerError as e:
            current_app.logger.error("execution log list can\'t be found ")
            abort(404, e.message)
        return execution_log

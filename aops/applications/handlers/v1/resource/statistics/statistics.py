# !/usr/bin/python
# -*- coding:utf-8 -*-

"""
@author: fengli
@time: 2018/8/21 下午3:43
@file: statistics
"""

from flask_restplus import Model
from flask_restplus import fields
from flask_restplus import reqparse
from flask_restplus import Resource
from flask_restplus import abort
from flask_restplus.namespace import Namespace
from flask import request, current_app as app
from aops.applications.database.apis.resource.statistics.statistics import count_hosts
from aops.applications.database.apis.resource.statistics.statistics import count_applications, number_file_commits, \
    count_risk_commands
from aops.applications.database.apis.repository.repository import Repostiory
from aops.applications.exceptions.exception import ResourcesNotFoundError
from aops.applications.common.scheduler_request import SchedulerApi
from aops.applications.exceptions.exception import SchedulerError


ns = Namespace('/v1/statistics', description='resources statistics')

statistics_resources_model = Model("statistics_resources_model", {
    'count': fields.Integer(required=True, description='The number of resources')
})

records_statistics_model = statistics_resources_model.clone('records_statistics_model', {
    'ratio': fields.String(required=True, description='The success ratio of resources'),
})

records_numbers_model = Model('RecordNumbers', {
    'date': fields.String(required=True, description='The statistics datetime'),
    'failed': fields.Integer(required=True, description='The number of failed'),
    'success': fields.Integer(required=True, description='The number of success')
})

statistics_risk_commands_model = Model("statistics_risk_commands_model", {
    'risks_count': fields.Integer(required=True, description='The number of resources'),
    'commands_count': fields.Integer(required=True, description='The number of resources')}
)
repository_resources_model = Model("statistics_repository_model", {
    'scripts_count': fields.Integer(required=True, description='The number of resources'),
    'applications_count': fields.Integer(required=True, description='The number of applications'),
    'configurations_count': fields.Integer(required=True, description='The number of resources')
})

repository_resources_model_with_date = repository_resources_model.clone("repository_resources_with_date", {
    'date': fields.String(description='The date of resources'),
})

records_top_model = Model('RecordTops', {
    'target_ip': fields.String(required=True, description='The statistics datetime'),
    'count': fields.Integer(required=True, description='The number of failed'),
})

top5_jobs_model = Model('JobTops', {
    'name': fields.String(description="job name"),
    'count': fields.Integer(description="count eg: 50"),
})

job_records_statistics_model = records_statistics_model.clone('job_records_statistics_model', {
    'top5': fields.List(fields.Nested(top5_jobs_model))
})


host_top_model = Model('HostTop', {
    'normal_count': fields.Integer(),
    'abnormal_count': fields.Integer(),
    'tops': fields.List(fields.Nested(records_top_model))
})

ns.add_model(statistics_resources_model.name, statistics_resources_model)
ns.add_model(records_statistics_model.name, records_statistics_model)
ns.add_model(job_records_statistics_model.name, job_records_statistics_model)

ns.add_model(records_numbers_model.name, records_numbers_model)
ns.add_model(repository_resources_model.name, repository_resources_model)
ns.add_model(statistics_risk_commands_model.name, statistics_risk_commands_model)
ns.add_model(repository_resources_model_with_date.name, repository_resources_model_with_date)

ns.add_model(records_top_model.name, records_top_model)
ns.add_model(host_top_model.name, host_top_model)
ns.add_model(top5_jobs_model.name, top5_jobs_model)


statistics_query_params = reqparse.RequestParser()
statistics_query_params.add_argument('start_time', type=str, location='args')
statistics_query_params.add_argument('end_time', type=str, location='args')


@ns.route('/hosts')
class StatisticsHosts(Resource):
    """
    statistic hosts resources
    """
    @ns.doc("query hosts resources info")
    @ns.response(404, 'no hosts resources can be found')
    @ns.expect(statistics_query_params)
    @ns.marshal_with(statistics_resources_model)
    def get(self):
        """ query hosts """
        args = statistics_query_params.parse_args()
        args.update(business=request.cookies.get('BusinessGroup', 'LDDS'))
        app.logger.debug(u"Statistic hosts with: {} begin".format(args))
        try:
            res = count_hosts(**args)
            app.logger.info(u"Statistic hosts succeed")
            return res, 200
        except ResourcesNotFoundError as e:
            app.logger.debug(u"Statistic hosts failed, reason: {}".format(e))
            abort(404, e.msg)


@ns.route('/applications')
class StatisticsApplications(Resource):
    """
    statistic applications resources
    """
    @ns.doc("query applications resources info")
    @ns.response(404, 'no applications resources can be found')
    @ns.expect(statistics_query_params)
    @ns.marshal_with(statistics_resources_model)
    def get(self):
        args = statistics_query_params.parse_args()
        args.update(business_group=request.cookies.get('BusinessGroup', 'LDDS'))
        app.logger.debug(u"Statistic applications with: {} begin".format(args))
        try:
            res = count_applications(**args)
            app.logger.info(u"Statistic applications succeed")
            return res, 200
        except ResourcesNotFoundError as e:
            app.logger.debug(u"Statistic applications failed, reason: {}".format(e))
            abort(404, e.msg)


@ns.route('/risk_commands')
class StatisticsRiskCommands(Resource):
    """
    statistic applications resources
    """
    @ns.doc("query applications resources info")
    @ns.response(404, 'no applications resources can be found')
    @ns.expect(statistics_query_params)
    @ns.marshal_with(statistics_risk_commands_model)
    def get(self):
        args = statistics_query_params.parse_args()
        args.update(business_group=request.cookies.get('BusinessGroup', 'LDDS'))
        app.logger.debug(u"Statistic applications with: {} begin".format(args))
        try:
            res = count_risk_commands(**args)
            app.logger.info(u"Statistic applications succeed")
            return res, 200
        except ResourcesNotFoundError as e:
            app.logger.debug(u"Statistic applications failed, reason: {}".format(e))
            abort(404, e.msg)


@ns.route('/repositories')
class StatisticsRepositories(Resource):
    """
    statistic repositories resources
    """
    @ns.doc("query applications resources info")
    @ns.response(404, 'no applications resources can be found')
    @ns.expect(statistics_query_params)
    @ns.marshal_with(repository_resources_model)
    def get(self):
        args = statistics_query_params.parse_args()
        args.update(business_group=request.cookies.get('BusinessGroup', 'LDDS'))
        app.logger.debug(u"Statistic applications with: {} begin".format(args))
        try:
            res = Repostiory().count_repository_projects(**args)
            app.logger.info(u"Statistic applications succeed")
            return res, 200
        except ResourcesNotFoundError as e:
            app.logger.debug(u"Statistic applications failed, reason: {}".format(e))
            abort(404, e.msg)


@ns.route('/file-commits')
class StatisticsFileCommits(Resource):
    """
    statistic risk command resources
    """
    @ns.doc("query applications resources info")
    @ns.response(404, 'no applications resources can be found')
    @ns.expect(statistics_query_params)
    @ns.marshal_list_with(repository_resources_model_with_date)
    def get(self):
        args = statistics_query_params.parse_args()
        args.update(business_group=request.cookies.get('BusinessGroup', 'LDDS'))
        app.logger.debug(u"Statistic file commits with: {} begin".format(args))
        try:
            res = number_file_commits(**args)
            app.logger.info(u"Statistic file commits succeed")
            return res, 200
        except ResourcesNotFoundError as e:
            app.logger.debug(u"Statistic file commits failed, reason: {}".format(e))
            abort(404, e.msg)


@ns.route('/job-records')
class StatisticsJobs(Resource):
    """
    statistic job execute records
    """
    @ns.doc("query job records info")
    @ns.response(404, 'no job records can be found')
    @ns.expect(statistics_query_params)
    @ns.marshal_with(job_records_statistics_model)
    def get(self):
        """ query job records """
        args = statistics_query_params.parse_args()
        args.update(business_group=request.cookies.get('BusinessGroup', 'LDDS'))
        app.logger.debug(u"Statistic job records with: {} begin".format(args))
        params = {key: value for key, value in args.items() if value is not None}
        try:
            res = SchedulerApi("/v1/jobs/statistics").get(params=params)
            app.logger.info(u"Statistic job records succeed")
            return res, 200
        except SchedulerError as e:
            app.logger.debug(u"Statistic job records failed, reason: {}".format(e))
            abort(404, e.msg)


@ns.route('/job-numbers')
class StatisticsJobNums(Resource):
    """
    statistic job execute number
    """
    @ns.doc("query job records info")
    @ns.response(404, 'no job records can be found')
    @ns.expect(statistics_query_params)
    @ns.marshal_list_with(records_numbers_model)
    def get(self):
        """ query job numbers """
        args = statistics_query_params.parse_args()
        args.update(business_group=request.cookies.get('BusinessGroup', 'LDDS'))
        app.logger.debug(u"Statistic job numbers with: {} begin".format(args))
        params = {key: value for key, value in args.items() if value is not None}
        try:
            res = SchedulerApi("/v1/jobs/numbers").get(params=params)
            app.logger.info(u"Statistic job numbers succeed")
            return res, 200
        except SchedulerError as e:
            app.logger.debug(u"Statistic the number of job records failed, reason: {}".format(e))
            abort(404, e.msg)


@ns.route('/flow-records')
class StatisticsFlows(Resource):
    """
    statistic flow execute records
    """
    @ns.doc("query flow records info")
    @ns.response(404, 'no flow records can be found')
    @ns.expect(statistics_query_params)
    @ns.marshal_with(records_statistics_model)
    def get(self):
        """ query flow records """
        args = statistics_query_params.parse_args()
        args.update(business_group=request.cookies.get('BusinessGroup', 'LDDS'))
        app.logger.debug(u"Statistic flow records with: {} begin".format(args))
        params = {key: value for key, value in args.items() if value is not None}
        try:
            res = SchedulerApi("/v1/flow-records/statistics").get(params=params)
            app.logger.info(u"Statistic flow records succeed")
            return res, 200
        except SchedulerError as e:
            app.logger.debug(u"Statistic flow records failed, reason: {}".format(e))
            abort(404, e.msg)


@ns.route('/flow-numbers')
class StatisticsJobNums(Resource):
    """
    statistic job execute number
    """
    @ns.doc("query flow records numbers")
    @ns.response(404, 'no flow records can be found')
    @ns.expect(statistics_query_params)
    @ns.marshal_with(records_numbers_model)
    def get(self):
        """ query job records """
        args = statistics_query_params.parse_args()
        args.update(business_group=request.cookies.get('BusinessGroup', 'LDDS'))
        app.logger.debug(u"Statistic job records with: {} begin".format(args))
        params = {key: value for key, value in args.items() if value is not None}
        try:
            res = SchedulerApi("/v1/flow-records/numbers").get(params=params)
            app.logger.info(u"Statistic flow records succeed")
            return res, 200
        except SchedulerError as e:
            app.logger.debug(u"Statistic flow records failed, reason: {}".format(e))
            abort(404, e.msg)


@ns.route('/jobs-top')
class StatisticsJobTimes(Resource):
    """
    statistic job execute number
    """
    @ns.doc("query job records info")
    @ns.response(404, 'no job records can be found')
    @ns.expect(statistics_query_params)
    @ns.marshal_list_with(records_top_model)
    def get(self):
        """ query top 10 job of the hosts """
        args = statistics_query_params.parse_args()
        args.update(business_group=request.cookies.get('BusinessGroup', 'LDDS'))
        app.logger.debug(u"Statistic job numbers with: {} begin".format(args))
        params = {key: value for key, value in args.items() if value is not None}
        try:
            res = SchedulerApi("/v1/jobs/tops").get(params=params)
            app.logger.info(u"Statistic job numbers succeed")
            return res, 200
        except SchedulerError as e:
            app.logger.debug(u"Statistic the number of job records failed, reason: {}".format(e))
            abort(404, e.msg)


@ns.route('/hosts-top')
class StatisticsUnusualHosts(Resource):
    """
    statistic daily inspection and host top
    """
    @ns.doc("query daily inspection and host top info")
    @ns.response(404, 'no  daily inspection and host top can be found')
    @ns.expect(statistics_query_params)
    @ns.marshal_list_with(host_top_model)
    def get(self):
        """ query daily inspection and host top info """
        args = statistics_query_params.parse_args()
        args.update(business_group=request.cookies.get('BusinessGroup', 'LDDS'))
        app.logger.debug(u"Statistic job numbers with: {} begin".format(args))
        params = {key: value for key, value in args.items() if value is not None}
        try:
            res = SchedulerApi("/v1/jobs/hosts").get(params=params)
            app.logger.info(u"Statistic job numbers succeed")
            return res, 200
        except SchedulerError as e:
            app.logger.debug(u"Statistic the number of job records failed, reason: {}".format(e))
            abort(404, e.msg)


if __name__ == '__main__':
    pass


#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 2018/7/19 13:35
# @Author  : szf

from flask import current_app as app, jsonify
from flask_restplus import Namespace, Model, fields, reqparse, Resource, abort

from aops.applications.handlers.v1.common import time_util
from aops.applications.handlers.v1.system.user.user import user_name_model

from aops.applications.database.apis import approve_config as approve_config_apis,\
    business_config as business_config_apis, alarm_config as alarm_config_apis, exchange_config as exchange_config_api

from aops.applications.exceptions.exception import ResourceNotFoundError, ResourceAlreadyExistError


ns = Namespace('/v1/sysconfigs', description='System Configuration')

# define models
approve_config_without_id_model = Model('ApproveConfigWithoutID', {
    'level': fields.Integer(required=True, default=1, unique=True, description='The level of task approved'),
    'script_on': fields.Integer(required=True, default=0, unique=True, description='Enable the approve of the script submit'),
    'software_on': fields.Integer(required=True, default=0, unique=True, description='Enable the approve of  software repository'),
    'config_on': fields.Integer(required=True, default=0, unique=True, description='Enable the approve of config repository')
})

approve_config_model = approve_config_without_id_model.clone('ApproveConfig', time_util, {
    'id': fields.Integer(readOnly=True, description='The approve config\'s identifier')
})

business_config_without_id_model = Model('BusinessConfigWithoutID', {
    'name': fields.String(required=True, unique=True, description='The business name'),
    'description': fields.String(required=True, unique=True, description='The business\' description')
})


business_config_model = business_config_without_id_model.clone('BusinessConfig', time_util, {
    'id': fields.Integer(readOnly=True, description='The business config\'s identifier')

})

daily_check_model = Model('DailyCheck', {
    'alarm_on': fields.Integer(required=True, unique=False, description='Enable the alarm'),
    'risk_alarm_to': fields.List(fields.Integer, description='The user id list'),
    'risk_alarm_by': fields.List(fields.String(unique=False, description='The ways to send alarms')),
    'except_alarm_to': fields.List(fields.Integer, description='The user id list'),
    'except_alarm_by': fields.List(fields.String(unique=False, description='The ways to send alarms'))
})
timed_job_model = Model('TimedJob', {
    'alarm_to': fields.List(fields.Integer, description='The user id list'),
    'alarm_on': fields.Integer(required=True, unique=False, description='Enable the alarm'),
    'alarm_by': fields.List(fields.String(required=True, unique=False, description='The ways to send alarms'))
})

alarm_config_without_id_model = Model('AlarmConfigWithoutID', {
    'daily_check': fields.Nested(daily_check_model),
    'timed_job': fields.Nested(timed_job_model)
})

alarm_config_model = alarm_config_without_id_model.clone('AlarmConfig', time_util, {
    'id': fields.Integer(readOnly=True, description='The alarm config\'s identifier')

})

exchange_config_without_id_model = Model('ExchangeConfigWithoutId', {
    'is_on': fields.Integer(description='The exchange config\'s identifier'),
    'start_time': fields.String(required=False, unique=False, description='Exchange start time'),
    'end_time': fields.String(required=False, unique=False, description='Exchange end time')
})

exchange_config_model = exchange_config_without_id_model.clone('ExchangeConfig', time_util, {
    'id': fields.Integer(readOnly=True, description='The exchange config\'s identifier')

})

sysconfig_without_id_model = Model('SystemConfigWithoutID', {
    'approve_config': fields.Nested(approve_config_without_id_model),
    'business_config': fields.List(fields.Nested(business_config_without_id_model)),
    'alarm_config': fields.Nested(alarm_config_without_id_model),
    'exchange_config': fields.Nested(exchange_config_without_id_model)
})

# register models
ns.add_model(sysconfig_without_id_model.name, sysconfig_without_id_model)
ns.add_model(approve_config_without_id_model.name, approve_config_without_id_model)
ns.add_model(business_config_without_id_model.name, business_config_without_id_model)
ns.add_model(alarm_config_without_id_model.name, alarm_config_without_id_model)
ns.add_model(exchange_config_without_id_model.name, exchange_config_without_id_model)
ns.add_model(exchange_config_model.name, exchange_config_model)
ns.add_model(timed_job_model.name, timed_job_model)
ns.add_model(daily_check_model.name, daily_check_model)
ns.add_model(business_config_model.name, business_config_model)


# define parsers
sysconfig_without_id_parser = reqparse.RequestParser()
sysconfig_without_id_parser.add_argument('approve_config', type=dict, location='json', required=True)
sysconfig_without_id_parser.add_argument('business_config', type=list, location='json', required=True)
sysconfig_without_id_parser.add_argument('alarm_config', type=dict, location='json', required=True)
sysconfig_without_id_parser.add_argument('exchange_config', type=dict, location='json', required=True)


@ns.route('/')
class SysConfigs(Resource):
    """
     Show or Update the system configuration
    """
    @ns.doc('Get system config')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'System config not found')
    @ns.marshal_with(sysconfig_without_id_model)
    def get(self):
        """
        Get system config item
        Return:
            the system config item
        """
        system_config = {}
        try:
            approve_configs = approve_config_apis.get_approve_configs()
            business_configs = business_config_apis.get_business_configs()
            alarm_configs = alarm_config_apis.get_alarm_config()
            exchange_configs = exchange_config_api.get_exchange_configs()

            system_config.update({
                'approve_config': approve_configs,
                'business_config': business_configs,
                'alarm_config': alarm_configs,
                'exchange_config': exchange_configs
            })
            app.logger.info("Get system config's result =======> {}".format(system_config))
        except ResourceNotFoundError as e:
            app.logger.error("No found the list of system configs")
            abort(404, e.message)

        return system_config

    @ns.doc('create system config')
    @ns.expect(sysconfig_without_id_model)
    @ns.marshal_with(sysconfig_without_id_model, code=201)
    def post(self):
        """
        create (or update) a system config item
        Returns:
            the new system config item
        """
        system_config = {}
        args = sysconfig_without_id_parser.parse_args()
        app.logger.debug("Create system config with params =======> {}".format(args))

        try:
            approve_config = approve_config_apis.create_approve_config(args.approve_config)
            business_config = business_config_apis.create_business_configs(args.business_config)
            alarm_config = alarm_config_apis.create_alarm_config(args.alarm_config)
            exchange_config = exchange_config_api.create_exchange_config(args.exchange_config)
        except ResourceAlreadyExistError as e:
            app.logger.error(e.message)
            abort(409, 'Already exist')
        system_config.update({
            'approve_config': approve_config,
            'business_config': business_config,
            'alarm_config': alarm_config,
            'exchange_config': exchange_config
        })
        app.logger.info("Create system config ========> {}".format(system_config))

        return system_config, 201


@ns.route('/businesses/')
class BusinessConfig(Resource):
    """
     Get all business config
    """
    @ns.doc('Get system business config')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'System business config not found')
    @ns.marshal_with(business_config_model)
    def get(self):
        """
        Get system business config items
        Return:
            the system business config items
        """

        try:
            business_configs = business_config_apis.get_business_configs()
            app.logger.info("Get business config's result =======> {}".format(business_configs))
        except ResourceNotFoundError as e:
            app.logger.error("No found the list of system business config")
            abort(404, e.message)

        return business_configs

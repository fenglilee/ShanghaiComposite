#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 2018/7/4 14:16
# @Author  : szf

import os
from flask import current_app as app, jsonify, request, session
from werkzeug.datastructures import FileStorage
from flask_restplus import Namespace, Model, fields, reqparse, Resource, abort

from aops.applications.common import parser
from aops.applications.handlers.v1.common import time_util
from aops.applications.handlers.v1.resource.application.application import application_model
from aops.applications.database.apis import host as host_api, group as group_api
from aops.applications.exceptions.exception import ResourceNotFoundError, ResourceAlreadyExistError, Error


ns = Namespace('/v1/hosts', description='Hosts operations')

ALLOWED_EXTENSIONS = set(['txt', 'CSV'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1] in ALLOWED_EXTENSIONS


# define models
accounts_without_id_model = Model('AccountWithoutID', {
   'username': fields.String(required=True, unique=True, description='The host account\'s username'),
   'password': fields.String(required=True, unique=True, description='The host account\'s password')

})

parameter_without_id_model = Model('ParameterWithoutID', {
   'name': fields.String(required=True, unique=True, description='The host parameter\'s name'),
   'value': fields.String(required=True, unique=True, description='The host parameter\'s value')

})

host_without_id_model = Model('HostWithoutID', {
    'name': fields.String(required=True, unique=True, description='The host\'s name'),
    'business': fields.String(required=True, unique=False, description='The host\'s business'),
    'type': fields.String(required=True, unique=True, description='The host\'s type'),
    'identity_ip': fields.String(required=True, unique=True, description='The host\'s identity ip'),
    #'internal_ip': fields.String(required=False, unique=True, description='The host\'s internal ip'),
    #'external_ip': fields.String(required=False, unique=True, description='The host\'s external ip'),
    #'special_ip': fields.String(required=False, unique=True, description='The host\'s special ip'),
    'description': fields.String(required=False, unique=False, description='The host\'s description'),
    'os': fields.String(required=False, unique=True, description='The host\'s OS'),
    'site': fields.String(required=False, unique=True, description='The host\'s site'),
    'cabinet': fields.String(required=False, unique=True, description='The host\'s cabinet'),
    'machine': fields.String(required=False, unique=True, description='The host\'s machine'),
    'accounts': fields.List(fields.Nested(accounts_without_id_model),
                            required=False, unique=False, description='The host\'s accounts'),
    'params': fields.List(fields.Nested(parameter_without_id_model),
                          required=False, unique=False, description='The host\'s parameters'),
    'apps': fields.List(fields.Nested(application_model),
                          required=False, unique=False, description='The host\'s apps')

})

host_update_model = Model('HostUpdateModel', {
    'accounts': fields.List(fields.Nested(accounts_without_id_model),
                            required=False, unique=False, description='The host\'s accounts'),
    'params': fields.List(fields.Nested(parameter_without_id_model),
                          required=False, unique=False, description='The host\'s parameters')
})

host_other_field_model = Model('HostOtherField', {
    'key_cn': fields.String(required=True, unique=False, description='The chinese key of host\'s other field'),
    'key_en': fields.String(required=True, unique=False, description='The english key of host\'s other field'),
    'value': fields.String(required=True, unique=False, description='The other field value')
})

host_model = host_without_id_model.clone('Host', time_util, {
    'id': fields.Integer(readOnly=True, description='The host\'s identifier'),
    'modified_by': fields.String(required=True, unique=False, description='The host\'s modified user'),
    'others': fields.List(fields.Nested(host_other_field_model))
    # 'others': fields.String()

})

host_with_other_field_model = host_model.clone('HostWithOtherField', {

})
host_ids_model = Model('HostIps', {
    'ids': fields.List(fields.String)
})

file_model = Model('UploadedFile', {
    'file': fields.String(required=True, unique=True, description='The file path shall be imported')
})

host_ip_model = Model('HostIP', {
    'id': fields.Integer(readOnly=True, description='The host\'s identifier'),
    'identity_ip': fields.String(required=True, unique=True, description='The identify ip of a host')
})

update_host_info_model = Model('UpdateHostInfo', {
    'deleted': fields.List(fields.Nested(host_model), required=True, unique=True, description='The deleted hosts'),
    'added': fields.List(fields.Nested(host_model), required=True, unique=True, description='The added hosts'),
    'updated': fields.List(fields.Nested(host_model), required=True, unique=True, description='The updated hosts')
})

update_account_model = Model('UpdateAccount', {
    'id': fields.Integer(readOnly=True, description='The host\'s identifier'),
    'name': fields.String(required=True, unique=True, description='The host name'),
    'identity_ip': fields.String(required=True, unique=True, description='The identify ip of a host')
})

# register models
ns.add_model(accounts_without_id_model.name, accounts_without_id_model)
ns.add_model(parameter_without_id_model.name, parameter_without_id_model)
ns.add_model(host_without_id_model.name, host_without_id_model)
ns.add_model(host_model.name, host_model)
ns.add_model(file_model.name, file_model)
ns.add_model(host_ip_model.name, host_ip_model)
ns.add_model(update_host_info_model.name, update_host_info_model)
ns.add_model(host_ids_model.name, host_ids_model)
ns.add_model(update_account_model.name, update_account_model)
ns.add_model(host_other_field_model.name, host_other_field_model)
ns.add_model(host_update_model.name, host_update_model)

# define parsers
host_without_id_parser = reqparse.RequestParser()
host_without_id_parser.add_argument('name')
host_without_id_parser.add_argument('business')
host_without_id_parser.add_argument('type')
host_without_id_parser.add_argument('identity_ip')
host_without_id_parser.add_argument('description')
host_without_id_parser.add_argument('os')
host_without_id_parser.add_argument('accounts', type=list, location='json', required=True)
host_without_id_parser.add_argument('params', type=list, location='json', required=True)
host_without_id_parser.add_argument('others')

host_parser = host_without_id_parser.copy()
host_parser.add_argument('id', type=int)

host_list_args = reqparse.RequestParser()
host_list_args.add_argument("business", type=str, location='args')
host_list_args.add_argument("fuzzy_query", type=str, location='args')

file_parser = reqparse.RequestParser()
file_parser.add_argument('file', location='files', type=FileStorage, required=True)


host_ids_parser = reqparse.RequestParser()
host_ids_parser.add_argument('ids', type=list, location='json')

host_update_parser = reqparse.RequestParser()
host_update_parser.add_argument('accounts', type=list, location='json', required=True)
host_update_parser.add_argument('params', type=list, location='json', required=True)


@ns.route('/')
class Hosts(Resource):
    """
    Show a list of all hosts, and lets you POST to add new hosts
    """

    @ns.doc('list_all_hosts')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'Host list not found')
    @ns.expect(host_list_args)
    @ns.marshal_list_with(host_model)
    def get(self):
        """
        list all hosts
        Returns:
             all hosts
        """
        args = host_list_args.parse_args()
        app.logger.debug("Get host list's params are: {}".format(args))
        try:
            hosts = host_api.get_hosts_list(business=args.identity_ip, fuzzy_query=args.fuzzy_query)
        except ResourceNotFoundError as e:
            app.logger.error("Host list can\'t be found with params: identity_ip={}, fuzzy_query={}". \
                             format(args.host_ip, args.fuzzy_query))
            abort(404, e.message)

        app.logger.info("Get host list's result {}".format(hosts))

        return hosts


@ns.route('/<string:identifier>')
@ns.param('identifier', 'The host\'s identifier, eg, \'1\' or \'a_1\'')
class Host(Resource):
    """
    Show a single host
    """

    @ns.doc('get_host')
    @ns.marshal_list_with(host_model)
    def get(self, identifier):
        """
        Get a host by identifier
        """
        app.logger.debug("Get host with identifier {}".format(identifier))
        host_id = str(identifier.split('_')[1]) if '_' in identifier else int(identifier)
        try:
            host = host_api.get_host_with_id(host_id)
        except ResourceNotFoundError as e:
            app.logger.error("No host found with identifier {}".format(identifier))
            abort(404, e.message)

        app.logger.debug("Get host {}".format(host))

        return host

    @ns.doc('update_host')
    @ns.expect(host_update_model)
    @ns.marshal_with(host_model, code=201)
    def put(self, identifier):
        """Update a host given its identifier"""
        try:
            host_info = host_update_parser.parse_args()
            app.logger.debug("update host with params {}".format(host_info))
            host_id = str(identifier.split('_')[1]) if '_' in identifier else int(identifier)

            updated_host = host_api.update_host_with_id(host_id, host_info)
            app.logger.info("update host {}".format(updated_host))

        except ResourceNotFoundError as e:
            app.logger.error("No found updated host with identifier {}".format(host_id))
            abort(404, e.message)

        return updated_host, 201


@ns.route('/ips/<string:business>')
@ns.param('business', 'The host\'s business, eg, LDDS, Cloud')
class HostIps(Resource):
    """
    Show host ips by business
    """
    @ns.doc('get_host ips')
    @ns.marshal_list_with(host_ip_model)
    def get(self, business):
        """
        Get host ips by business
        """
        try:
            host_ips = host_api.get_host_ips_with_business(business)
            app.logger.info("Get host ips {}".format(host_ips))
        except ResourceNotFoundError as e:
            app.logger.error("No host found host ips  {}".format(host_ips))
            abort(404, e.message)
        return host_ips


@ns.route('/accounts')
class ImportAccount(Resource):
    """
    Import host accounts by uploaded file
    """
    @ns.doc('import host accounts')
    @ns.expect(file_parser)
    @ns.marshal_list_with(update_account_model)
    def post(self):
        """
        Update the hosts' accounts by uploaded file
        """
        args = file_parser.parse_args()
        business = request.cookies.get('BussinessGroup')
        app.logger.debug("Get import host account args {} in bussiness {}".format(args, business))
        try:
            uploaded_file = args['file']
            if uploaded_file and allowed_file(uploaded_file.filename):
                FILE_DIR = os.path.join(app.root_path, 'upload_files', 'host')
                server_path = os.path.join(FILE_DIR, uploaded_file.filename)
                uploaded_file.save(server_path)
            host_accounts = parser.TextParser(server_path).parse()
            app.logger.info('Host accounts from file ====> {}'.format(host_accounts))
            hosts = host_api.sync_host_accounts(host_accounts, business)
            app.logger.info('Host accounts Sync to DB ====> {}'.format(hosts))
        except Error as e:
            app.logger.error("Import host account Error {}".format(e.message))
            abort(404, e.message)

        app.logger.debug("Imported  host account {}".format(hosts))

        return hosts


@ns.route('/infos')
class ImportInformation(Resource):
    """
    Import host information by uploaded file, except accounts
    """
    @ns.doc('import host information, excluding host accounts')
    @ns.expect(file_parser)
    @ns.marshal_with(update_host_info_model)
    def post(self):
        """
        update hosts' basic information by uploaded file
        """
        args = file_parser.parse_args()
        business = request.cookies.get('BussinessGroup')
        login_name = session.get('user_info').get('user')
        business = business or 'LDDS'

        app.logger.debug("Get import host information args {}".format(args))
        try:
            uploaded_file = args['file']
            if uploaded_file and allowed_file(uploaded_file.filename):
                FILE_DIR = os.path.join(app.root_path, 'upload_files', 'host')
                server_path = os.path.join(FILE_DIR, uploaded_file.filename)
                uploaded_file.save(server_path)
            hosts_items = parser.CsvParser(server_path).parse()
            sync_hosts = host_api.sync_hosts_info(hosts_items, business, login_name)
        except Error as e:
            app.logger.error("Import host information Error {}".format(e.message))
            abort(404, e.message)

        app.logger.debug("Imported  host information {}".format(sync_hosts))

        return sync_hosts


@ns.route('/cmdb')
class SyncCMDB(Resource):
    """
    Sync host information with CMDB by Restful API
    """
    @ns.doc('fetch host information')
    @ns.marshal_with(update_host_info_model)
    def post(self):
        """
        Sync host information with CMDB
        """
        business = request.cookies.get('BussinessGroup')
        login_name = session.get('user_info').get('user')
        business = business or 'LDDS'
        try:
            results = host_api.sync_host_with_cmdb(business, login_name)
        except Error as e:
            app.logger.error("Sync hosts with CMDB", e.message)
            abort(404, e.message)

        return results, 200


@ns.route('/scheduler/')
class SyncScheduler(Resource):
    """
    Sync total host information with Scheduler by Restful API
    """
    @ns.doc('sync host information with Scheduler')
    def post(self):
        """
        Sync host information with Scheduler
        """
        business = request.cookies.get('BussinessGroup')
        business = business or 'LDDS'
        app.logger.info("Sync hosts with scheduler args: {}".format(business))
        try:
            results = group_api.sync_all_groups_with_scheduler(business)
            app.logger.info("Sync hosts with scheduler result: {}".format(results))
        except Error as e:
            app.logger.error("Sync hosts with scheduler", e.message)
            abort(404, e.message)

        return results, 200


@ns.route('/todo-ips')
class HostIps(Resource):
    """
    Get the tree groups
    """

    @ns.doc('get host ip list')
    @ns.expect(host_ids_model)
    def post(self):
        """
        Get the tree groups
        """
        args = host_ids_parser.parse_args()
        app.logger.info('get host ip args {}'.format(args))
        try:
            host_ips = host_api.get_host_ips_with_ids(args.ids)
            app.logger.info("Get tree ips {}".format(host_ips))
        except ResourceNotFoundError as e:
            app.logger.warning("No tree ips found !!", e.message)
            abort(404, e.message)

        result = jsonify(host_ips)

        return result
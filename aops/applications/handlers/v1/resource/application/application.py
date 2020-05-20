#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 2018/7/19 16:53
# @Author  : szf
import datetime
from flask import current_app as app, jsonify
from flask_restplus import Namespace, Model, fields, reqparse, Resource, abort

from aops.applications.handlers.v1.common import time_util, full_time_util
from aops.applications.handlers.v1.common import pagination_base_model
from aops.applications.handlers.v1.utils import to_dynamic_dict
from aops.applications.database.apis.resource.application import application as app_apis
from aops.applications.exceptions.exception import ResourceNotFoundError, ResourcesNotFoundError,\
    Error, ResourceAlreadyExistError, ResourceNotUpdatedError


ns = Namespace('/v1/appliations', description='Application Instances Management')

# define models
parameter_model = Model('Parameter', {
    'name': fields.String(required=True, unique=False, description='The name of parameter'),
    'value': fields.String(required=True, unique=False, description='The name of parameter')
})

application_without_id_model = Model('ApplicationWithoutID', {
    'instance_name': fields.String(required=True, unique=True, description='The name of application instance'),
    'instance_description': fields.String(required=True, unique=True, description='The description of application instance'),
    'name': fields.String(required=True, unique=True, description='The name of application'),
    'version': fields.String(required=True, unique=True, description='The application version'),
    'type': fields.String(required=True, unique=True, description='The application type'),
    'language': fields.String(required=True, unique=True, description='The application language'),
    'sw_package_repository': fields.String(required=True, unique=True, description='The path of software packages\' repository'),
    'cfg_file_repository': fields.String(required=True, unique=True, description='The path of config files\' repository'),
    'parameters': fields.List(fields.Nested(parameter_model), description='The predefined parameters of applications'),
})

application_model = application_without_id_model.clone('Application', full_time_util, {
    'id': fields.Integer(readOnly=True, description='The application\'s identifier'),
    'inst_id_cmdb': fields.Integer(description='The application\'s identifier in CMDB'),
    'instance_status': fields.Integer(required=True, unique=True,
                                      description='The status of application instance,\
                                       0: new, 1: modified 2: published, 3: offline'),
    'creator': fields.String(required=True, unique=True, description='The name of application creator'),
    'host_ips': fields.List(
        fields.String(required=True, unique=True, description='The host ips of the application publish')),
    'publisher': fields.String(required=True, unique=True, description='The name of application publisher'),
    'publish_time': fields.String(required=True, unique=True, description='The published time of applications'),
    'others': fields.String(required=True, unique=True, description='The other fields')

})

application_ids_model = Model('AppInstanceIds', {
    'app_ids': fields.List(fields.Integer, description='The ids of application instance')
})

application_pagination_model = pagination_base_model.clone("ApplicationPagination", {
    "items": fields.List(fields.Nested(application_model))
})

app_property_model = Model('AppProperty', {
    'instance_name': fields.String(required=True, unique=True, description='The name of application instance'),
    'type': fields.String(required=True, unique=True, description='The application type'),
    'instance_status': fields.Integer(required=True, unique=True,
                                      description='The status of application instance, 0: new, 1: modified 2: published, 3: offline'),
    'name': fields.String(required=True, unique=True, description='The name of application'),
    'version': fields.String(required=True, unique=True, description='The application version'),
    'creator': fields.String(required=True, unique=True, description='The name of application creator'),
    'publisher': fields.String(required=True, unique=True, description='The name of application publisher')
})

app_type_item_model = Model('AppTypeItem', {
    'id': fields.Integer(readOnly=True, description='The application\'s type identifier'),
    'label': fields.String(required=True, description='The all application types in the system')
})

app_type_model = Model('AppType', {
    'app_types': fields.List(fields.Nested(app_type_item_model))
})

app_language_model = Model('Language', {
    'app_languages': fields.List(fields.String, description='The all application languages in the system')
})

# register models
ns.add_model(parameter_model.name, parameter_model)
ns.add_model(application_model.name, application_model)
ns.add_model(application_without_id_model.name, application_without_id_model)
ns.add_model(application_ids_model.name, application_ids_model)
ns.add_model(application_pagination_model.name, application_pagination_model)
ns.add_model(app_property_model.name, app_property_model)
ns.add_model(app_type_model.name, app_type_model)
ns.add_model(app_type_item_model.name, app_type_item_model)
ns.add_model(app_language_model.name, app_language_model)


# define parsers
application_without_id_parser = reqparse.RequestParser()
application_without_id_parser.add_argument('instance_name')
application_without_id_parser.add_argument('instance_description')
# application_without_id_parser.add_argument('instance_status')
application_without_id_parser.add_argument('name', help='The application name')
application_without_id_parser.add_argument('version')
application_without_id_parser.add_argument('type', help='The application type')
application_without_id_parser.add_argument('language')
# application_without_id_parser.add_argument('creator')
application_without_id_parser.add_argument('parameters', type=list, location='json', required=False)
application_without_id_parser.add_argument('sw_package_repository')
application_without_id_parser.add_argument('cfg_file_repository')
# application_without_id_parser.add_argument('host_ips', type=list, location='json', required=True)
# application_without_id_parser.add_argument('publisher')
# application_without_id_parser.add_argument('publish_time')

application_parser = application_without_id_parser.copy()
application_parser.add_argument('id', type=int)

application_ids_parser = reqparse.RequestParser()
application_ids_parser.add_argument('app_ids', type=list, location='json')

app_list_args = reqparse.RequestParser()
app_list_args.add_argument("page", type=int, location='args', required=True, help='Current page number.')
app_list_args.add_argument("per_page", type=int, location='args', required=True, help='The number of items in a page.')
app_list_args.add_argument('name', type=str, location='args')
app_list_args.add_argument('type', type=str, location='args')
app_list_args.add_argument('version', type=str, location='args')
app_list_args.add_argument('creator', type=str, location='args')
app_list_args.add_argument('publisher', type=str, location='args')
app_list_args.add_argument('instance_status', type=int, location='args', help='The instance status')
app_list_args.add_argument('instance_name', type=str, location='args', help='Application instance name')
app_list_args.add_argument('start_time', type=str, location='args', help='The start time of publishing an instance')
app_list_args.add_argument('end_time', type=str, location='args', help='The end time of publishing an instance')
app_list_args.add_argument('fuzzy_query', type=str, location='args')

app_property_args = reqparse.RequestParser()
app_property_args.add_argument('instance_name')
app_property_args.add_argument('name')
app_property_args.add_argument('type')
app_property_args.add_argument('version')
app_property_args.add_argument('creator')
app_property_args.add_argument('publisher')
app_property_args.add_argument('instance_status')


@ns.route('/')
class Applications(Resource):
    @ns.doc('Get application instance list')
    @ns.response(200, 'Application pagination list')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'applications not found')
    @ns.expect(app_list_args)
    @ns.marshal_list_with(application_pagination_model)
    def get(self):
        """
        get application list

        Return:
             the application list
        """
        args = app_list_args.parse_args()
        app.logger.debug("Get application list with params {}".format(args))
        try:
            applications = app_apis.get_application_list(args.page, args.per_page,
                                                         name=args.name,
                                                         type=args.type,
                                                         version=args.version,
                                                         creator=args.creator,
                                                         publisher=args.publisher,
                                                         instance_status=args.instance_status,
                                                         instance_name=args.instance_name,
                                                         start_time=args.start_time,
                                                         end_time=args.end_time)
        except ResourceNotFoundError as e:
            app.logger.error("No found the list of applications")
            abort(404, e.message)

        app.logger.info("Get application list's result {}".format(applications))

        return applications

    @ns.doc('create application instances')
    @ns.expect(application_without_id_model)
    @ns.marshal_with(application_model, code=201)
    def post(self):
        """
        create a application instance item
        Returns:
            the new application instance item
        """
        args = application_without_id_parser.parse_args()
        # args.parameters = to_dynamic_dict(args.parameters)
        app.logger.debug("Create application with params {}".format(args))

        try:
            application = app_apis.create_application(args)
        except ResourceAlreadyExistError as e:
            app.logger.error(e.message)
            abort(409, 'Already exist')

        app.logger.info("Create application {}".format(application))
        return application, 201

    @ns.doc('delete application instances')
    @ns.expect(application_ids_model)
    @ns.marshal_list_with(application_model, code=201)
    def delete(self):
        """
        delete multiple application instances
        Returns:
            the deleted application instances
        """
        args = application_ids_parser.parse_args()

        app.logger.debug(u"Delete application item with application ids: {}".format(args.app_ids))
        try:
            deleted_apps = app_apis.delete_applications_with_ids(args.app_ids)
            app.logger.info(u'Deleted applications {} '.format(deleted_apps))
        except ResourcesNotFoundError as e:
            app.logger.error(e.message)
            abort(404, u"{}".format(e.message))
        except Error as e:
            app.logger.error(e.message)
            abort(403, u"{}".format(e.msg))

        return deleted_apps, 200


@ns.route('/<int:identifier>')
@ns.param('identifier', 'The application\'s identifier')
class Application(Resource):
    """
    Show a application
    """
    @ns.doc('get application by identifier')
    @ns.marshal_with(application_model)
    def get(self, identifier):
        """
        Get a application by identifier
        """
        app.logger.debug("Get application with identifier {}".format(identifier))

        try:
            application = app_apis.get_application_with_id(identifier)

        except ResourceNotFoundError as e:
            app.logger.error("No found application with identifier {}".format(identifier))
            abort(404, e.message)

        app.logger.debug("Get application {}".format(application))

        return application

    # @ns.doc('delete application by identifier')
    # @ns.marshal_with(application_model, code=201)
    # def delete(self, identifier):
    #     """
    #     delete a application instance by identifier.
    #
    #     Return:
    #          the deleted application instance
    #     """
    #     app.logger.debug("Delete application with identifier {}".format(identifier))
    #     try:
    #         deleted_application = app_apis.delete_application_with_id(identifier)
    #         app.logger.debug("Delete application {}".format(deleted_application))
    #     except Error as e:
    #         app.logger.error("Deleted application {} failed".format(e.code))
    #         abort(e.code, e.msg)
    #
    #     return deleted_application

    @ns.doc('update application by identifier')
    @ns.expect(application_without_id_model)
    @ns.marshal_with(application_model, code=201)
    def put(self, identifier):
        """Update a application given its identifier"""
        app_info = application_without_id_parser.parse_args()
        app_info.parameters = to_dynamic_dict(app_info.parameters)

        app.logger.debug("update application with params {}".format(app_info))
        try:
            updated_app_info = app_apis.update_application_with_id(identifier, app_info)
            app.logger.info("update application  {}".format(updated_app_info))

        except (ResourcesNotFoundError, ResourceNotUpdatedError) as e:
            app.logger.error("Update application {} failed".format(e.message))
            abort(403, u'{}'.format(e.message))

        return updated_app_info, 201


@ns.route('/search')
class ApplicationFilters(Resource):
    """
       Application filters information
    """
    @ns.doc('filter list ')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'Application list not found')
    @ns.expect(app_property_args)
    @ns.marshal_list_with(app_property_model)
    def get(self):
        """Get a application list by search"""
        args = app_property_args.parse_args()
        instance_name = args.instance_name
        name = args.name
        type = args.type
        version = args.version
        instance_status = args.instance_status
        creator = args.creator
        publisher = args.publisher

        ############################################################
        # check the number of args, and only one parameter permission
        #############################################################
        app.logger.debug("application search with params {}".format(args))
        try:
            apps = app_apis.get_application_list_search(instance_name=instance_name,
                                                        name=name,
                                                        type=type,
                                                        version=version,
                                                        instance_status=instance_status,
                                                        creator=creator,
                                                        publisher=publisher)
            app.logger.info("Get application list's result with {}".format(apps))
        except ResourceNotFoundError as e:
            app.logger.error("application list can\'t be found ")
            abort(404, e.message)
        return apps


@ns.route('/types')
class ApplicationTypes(Resource):
    """
       Application types information
    """
    @ns.doc('All types list in system')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'Application types not found')
    @ns.marshal_with(app_type_model)
    def get(self):
        """Get all application types in the system"""

        try:
            types = app.config['APP_TYPES'] if app.config['APP_TYPES'] else []
            app.logger.info("Get all application types's result with {}".format(types))
        except Error as e:
            app.logger.error("application types can\'t be found ")
            abort(404, e.message)
        return {'app_types': types}


@ns.route('/languages')
class ApplicationLanguages(Resource):
    """
       Application languages information
    """

    @ns.doc('All types list in system')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'Application languages not found')
    @ns.marshal_list_with(app_language_model)
    def get(self):
        """Get all application languages in the system"""

        try:
            languages = app.config['APP_LANGUAGES'] if app.config['APP_LANGUAGES'] else []
            app.logger.info("Get all application languages' result with {}".format(languages))
        except Error as e:
            app.logger.error("application languages can\'t be found ")
            abort(404, e.message)
        return {'app_languages': languages}


@ns.route('/list')
class ApplicationList(Resource):
    @ns.doc('Get application instance list')
    @ns.response(200, 'Application pagination list')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'applications not found')
    @ns.marshal_list_with(application_model)
    def get(self):
        """
        get application list

        Return:
             the application list
        """
        try:
            applications = app_apis.get_applications_list()
        except ResourceNotFoundError as e:
            app.logger.error("No found the list of applications")
            abort(404, e.message)

        app.logger.info("Get application list's result {}".format(applications))

        return applications


@ns.route('/app-online/<int:identifier>')
class ApplicationOnline(Resource):
    @ns.doc('update application publish by identifier')
    #@ns.marshal_with(application_model)
    def put(self, identifier):
        """
        update application stats into published

        Return:
             the application instance
        """
        app.logger.info("update application's args {}".format(identifier))
        try:
            instance = app_apis.update_online_with_id(identifier, None)
        except ResourceNotFoundError as e:
            app.logger.error("No found the list of applications")
            abort(404, e.message)

        app.logger.info("update application 's result {}".format(instance))

        return jsonify(instance)


@ns.route('/app-offline/<int:identifier>')
class ApplicationOffline(Resource):
    @ns.doc('update application publish by identifier')
    #@ns.marshal_with(application_model)
    def put(self, identifier):
        """
        update application stats into published

        Return:
             the application instance
        """
        app.logger.info("update application offline 's args {}".format(identifier))
        try:
            instance = app_apis.update_offline_with_id(identifier, None)
        except ResourceNotFoundError as e:
            app.logger.error("No found the list of applications")
            abort(404, e.message)

        app.logger.info("update application offline 's result {}".format(instance))

        return jsonify(instance)

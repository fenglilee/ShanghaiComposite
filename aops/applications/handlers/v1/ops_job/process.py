#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 2018/7/28 13:24
# @Author  : szf

from flask import current_app as app
from flask_restplus import Namespace, Model, fields, reqparse, Resource, abort

from aops.applications.handlers.v1.common import full_time_util, time_util, pagination_base_model
from aops.applications.database.apis import process as process_api, process_execution as timed_process_api
from aops.applications.exceptions.exception import ResourceNotFoundError, ResourcesNotFoundError, ResourceAlreadyExistError, Error

ns = Namespace('/v1/processes', description='Processes operations')

##############################################
#
# define models
#
###############################################

process_without_id_model = Model('ProcessWithoutID', {
    'name': fields.String(required=True, description='The process\'s name'),
    'description': fields.String(required=True, description='The process\'s description'),
    'status': fields.Integer(required=True, default=0, description='Is this process enabled'),
    'scheduling': fields.String(required=True, description='The process\'s scheduling including the job/tasks'),
    # 'business_group': fields.String(required=True, description='The process\'s business group'),
    'has_manual_job': fields.Integer(required=True, default=0, description='Is there manul job or not'),
    'job_id_list': fields.List(fields.Integer, description='The id list for job templates')
})

process_model = process_without_id_model.clone('Process', full_time_util, {
    'id': fields.Integer(readOnly=True, description='The process\'s identifier'),
    'creator': fields.String(required=True, description='The process\'s creator'),
    'success_rate': fields.Integer(required=False, default=0, description='The process\'s success rate'),
    'risk_level': fields.Integer(required=True, description='The process\'s risk level'),
    'execution_account': fields.Integer(required=True, description='The process\'s risk level')
})

process_pagination_model = pagination_base_model.clone('ProcessPagination', {
    'items': fields.List(fields.Nested(process_model))
})

process_ids_model = Model('ProcessIds', {
    'process_ids': fields.List(fields.Integer, description='process id list')
})

process_ids_status_model = process_ids_model.clone('ProcessIdsStatus', {
    'status': fields.Integer(required=True, description='Are these processes enabled')
})

process_update_model = process_without_id_model.clone('ProcessUpdateModel')

process_filter_list_model = Model('ProcessFilterList', {
    'process_names': fields.List(fields.String),
    'creators': fields.List(fields.String),
    'job_names': fields.List(fields.String)
})

process_copy_model = Model('ProcessCopy', {
    'name': fields.String(required=True, description='The copied process\'s name'),
    'description': fields.String(required=True, description='The copied process\'s description'),
    'status': fields.Integer(required=True, default=0, description='Is this copied process enabled')
})

creator_model = Model('ProcessCreator', {
    'creator': fields.List(fields.String)
})

##############################################
#
#  register models
#
###############################################
""" process related models """
ns.add_model(process_model.name, process_model)
ns.add_model(process_without_id_model.name, process_without_id_model)
ns.add_model(process_pagination_model.name, process_pagination_model)
ns.add_model(process_ids_model.name, process_ids_model)
ns.add_model(process_ids_status_model.name, process_ids_status_model)
ns.add_model(process_update_model.name, process_update_model)
ns.add_model(process_filter_list_model.name, process_filter_list_model)
ns.add_model(process_copy_model.name, process_copy_model)
ns.add_model(creator_model.name, creator_model)

##############################################
#
# define request parsers
#
###############################################

""" process related parsers"""
process_list_args = reqparse.RequestParser()
process_list_args.add_argument('page', type=int, location='args', required=True, help='Current page number.')
process_list_args.add_argument('per_page', type=int, location='args', required=True, help='The number of items in a page.')
process_list_args.add_argument('name', location='args')
process_list_args.add_argument('creator', location='args')
process_list_args.add_argument('start_time', location='args')
process_list_args.add_argument('end_time', location='args')
process_list_args.add_argument('job_id', location='args', help='The job id used to ilter processes')

process_without_id_parser = reqparse.RequestParser()
process_without_id_parser.add_argument('name')
process_without_id_parser.add_argument('creator')
process_without_id_parser.add_argument('description')
process_without_id_parser.add_argument('status')
process_without_id_parser.add_argument('scheduling')
process_without_id_parser.add_argument('has_manual_job', type=int)
process_without_id_parser.add_argument('job_id_list', type=list, location='json')

process_parser = process_without_id_parser.copy()
process_parser.add_argument('id', type=int)

process_ids_parser = reqparse.RequestParser()
process_ids_parser.add_argument('process_ids', type=list, location='json')

process_ids_status_parser = process_ids_parser.copy()
process_ids_status_parser.add_argument('status', type=int)  # 0: disabled 1: enabled

process_update_parser = process_without_id_parser.copy()

process_filter_list_parser = reqparse.RequestParser()
process_filter_list_parser.add_argument('process_names')
process_filter_list_parser.add_argument('creators')
process_filter_list_parser.add_argument('job_names')

process_copy_parser = reqparse.RequestParser()
process_copy_parser.add_argument('name')
process_copy_parser.add_argument('status')
process_copy_parser.add_argument('description')


##################################################
#
# process related resources
#
###################################################
@ns.route('/')
class Processes(Resource):
    """
    Show a list of process, create a new process and delete or update multiple process
    """
    @ns.doc('list all processes')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'Process list not found')
    @ns.expect(process_list_args)
    @ns.marshal_list_with(process_pagination_model)
    def get(self):
        """
        Get the process items list.
        Return:
             the process items list
        """
        args = process_list_args.parse_args()
        app.logger.debug("Get process list's params are: {}".format(args))

        try:
            process = process_api.get_process_list(args.page, args.per_page,
                                                   process_name=args.name,
                                                   creator=args.creator,
                                                   start_time=args.start_time,
                                                   end_time=args.end_time,
                                                   job_id=args.job_id)
            app.logger.info("Get process list's result with page num {}, and length is {}".format(args.page, len(process.items)))

        except ResourcesNotFoundError as e:
            app.logger.error(
                "Processes list can\'t be found with params: page={}, per_page={}".format(args.page, args.per_page))
            abort(404, e.message)
        return process

    @ns.doc('create process')
    @ns.expect(process_without_id_model)
    @ns.marshal_with(process_model, code=200)
    def post(self):
        """
        Create a process item
        Return:
            the new process item
        """
        args = process_parser.parse_args()
        app.logger.debug("Create process item's params are: {}".format(args))
        try:
            created_process = process_api.create_process(args)
        except ResourceAlreadyExistError as e:
            app.logger.error("{} this process name already exists".format(args.name))
            abort(403, 'Already exists')
        app.logger.info("Created process item's result is: {}".format(created_process))

        return created_process

    @ns.doc('delete multiple timed processes')
    @ns.expect(process_ids_model)
    @ns.marshal_with(process_model, code=201)
    def delete(self):
        """
        Delete multiple process items
        Return:
            the deleted process items
        """
        args = process_ids_parser.parse_args()
        app.logger.debug("Delete process item with process ids: {}".format(args.process_ids))
        try:
            deleted_processes = process_api.delete_processes_with_ids(args.process_ids)
        except Error as e:
            app.logger.error('Delete processes')
            abort(403, 'Delete processes')
        app.logger.debug('Deleted processes {} '.format(deleted_processes))

        return deleted_processes, 200

    @ns.doc('enable or disable processes')
    @ns.expect(process_ids_status_model)
    @ns.marshal_with(process_model, code=201)
    def put(self):
        """
        Enable or disable multiple processes
        Return:
            the operational process
        """
        args = process_ids_status_parser.parse_args()
        try:
            updated_processes = process_api.update_status_with_ids(args.process_ids, args.status)
        except Error as e:
            app.logger.error('Update status for processes', e.message)
            abort(403, 'Update processes')
        app.logger.debug('Update processes {} '.format(updated_processes))

        return updated_processes, 200


@ns.route('/<int:identifier>')
@ns.response(404, 'Process not found')
@ns.param('identifier', 'The process\'s identifier')
class Process(Resource):
    """
    Show a single process, delete and update it.
    """
    @ns.doc('Get single process item')
    @ns.marshal_with(process_model)
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
            process = process_api.get_process_with_id(identifier)
            app.logger.info("Get process item with id {} 's result is: {}".format(identifier, process.to_dict()))
        except ResourceNotFoundError as e:
            app.logger.error("process item can\'t be found with id {}".format(identifier))
            abort(404, e.message)
        return process

    @ns.doc('create process')
    @ns.expect(process_copy_model)
    @ns.marshal_with(process_model, code=200)
    def post(self, identifier):
        """
        Copy a process
        Return:
            the copied process
        """
        args = process_copy_parser.parse_args()
        app.logger.debug("Copy a process item with id: {}, args: {}".format(identifier, args))
        try:
            copied_process = process_api.copy_process(identifier, args)
            app.logger.info("The copied process item {}".format(copied_process))
        except Error as e:
            app.logger.error("The copied process item {}".format(e.message))
            abort(404, e.message)
        return copied_process

    @ns.doc('Delete single process item')
    @ns.marshal_with(process_model)
    @ns.response(200, 'Delete single process item')
    def delete(self, identifier):
        """
        Delete a given process with identifier
        Args:
            identifier: process id
        Return:
            the deleted process item
        """
        app.logger.debug("Delete a process item with id: {}".format(identifier))
        try:
            process = process_api.delete_process_with_id(identifier)
            app.logger.info("Delete process item with id {} 's result is: {}".format(identifier, process.to_dict()))
        except ResourceNotFoundError as e:
            app.logger.error("The process item can\'t be found with id {}".format(identifier))
            abort(404, e.message)

        return process

    @ns.expect(process_update_model)
    @ns.response(200, 'Process updated')
    @ns.marshal_with(process_model)
    def put(self, identifier):
        """
        Update a given process with identifier
        Args:
            identifier: process id
        Return:
            the updated process item
        """
        args = process_update_parser.parse_args()
        app.logger.debug("update process with params {}, identifier {}".format(args, identifier))
        try:
            updated_process = process_api.update_process_with_id(identifier, args)
            app.logger.debug("update process {}".format(updated_process))
        except ResourceNotFoundError as e:
            app.logger.error("No found updated process with identifier {}".format(identifier))
            abort(404, e.message)

        return updated_process


@ns.route('/filters/')
class ProcessFilters(Resource):
    """
       Process filters information
    """
    @ns.doc('filter list ')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'Filter list not found')
    @ns.marshal_list_with(process_filter_list_model)
    def get(self):
        """Get all filter lists"""
        try:
            filters = process_api.get_filter_list()
            app.logger.info("Get filter list's result with {}".format(filters))
        except ResourcesNotFoundError as e:
            app.logger.error("filter list can\'t be found ")
            abort(404, e.message)
        return filters


@ns.route('/creator/')
class ProcessCreator(Resource):
    """
    Screening job
    """

    @ns.doc('list_creator')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'creator list not found')
    @ns.marshal_with(creator_model)
    def get(self):
        """Get all creator"""
        try:
            creators = process_api.get_creator_list()
            app.logger.info("Get creator list's result with {}".format(creators))
        except ResourcesNotFoundError as e:
            app.logger.error("creator list can\'t be found ")
            abort(404, e.message)
        return creators

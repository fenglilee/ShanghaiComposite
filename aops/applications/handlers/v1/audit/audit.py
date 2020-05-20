#!/usr/bin/env python
# -*- coding:utf-8 -*-
from flask import current_app as app
from flask import stream_with_context
from flask import abort
from flask import Response
from datetime import datetime
from flask_restplus import Namespace, Resource, Model, fields, reqparse
from aops.applications.handlers.v1.common import time_util, pagination_base_model
from aops.applications.exceptions.exception import ResourcesNotFoundError
from aops.applications.database.apis.audit.audit import get_audit_list, audit_list_search, get_audit_user_list, \
    get_audit_resource_list, get_audits_csv

ns = Namespace('/v1/audits', description='permission audit records')


audit_model = time_util.clone('PermissionAudit', {
    'id': fields.Integer(readOnly=True, description='The file\'s identifier'),
    'user': fields.String(required=True),
    'source_ip': fields.String(required=True),
    'resource': fields.String(required=True),
    'resource_id': fields.Integer(required=True),
    'operation': fields.String(required=True),
    'status': fields.Integer(required=True, description='The task\'s risk level'),
    'message': fields.String(required=True, description='The file\' risk statement'),
})


audit_pagination_model = pagination_base_model.clone("AuditPagination", {
    "items": fields.List(fields.Nested(audit_model))
})

audit_creator_model = Model('AuditCreator', {
    'creator': fields.List(fields.String)
})

audit_resource_model = Model('AuditResource', {
    'resource': fields.List(fields.String)
})

ns.add_model(audit_pagination_model.name, audit_pagination_model)
ns.add_model(audit_model.name, audit_model)
ns.add_model(audit_resource_model.name, audit_resource_model)
ns.add_model(audit_creator_model.name, audit_creator_model)

pagination_args = reqparse.RequestParser()
pagination_args.add_argument('page', type=int, location='args', required=True, help='Current page number.')
pagination_args.add_argument("per_page", type=int, location='args', required=True, help='The number of items in a page.')
pagination_args.add_argument('fq', type=str, location='args', dest="fuzzy_query")

audit_list_args = pagination_args.copy()
audit_list_args.add_argument('start_time', type=str, location='args')
audit_list_args.add_argument('end_time', type=str, location='args')
audit_list_args.add_argument('user', type=str, location='args', help="user name")
audit_list_args.add_argument('source_ip', type=str, location='args')
audit_list_args.add_argument('resource_type', type=str, location='args')
audit_list_args.add_argument('resource_id', type=str, location='args')
audit_list_args.add_argument('operation', type=str, location='args')
audit_list_args.add_argument('status', type=str, location='args')
audit_list_args.add_argument('message', type=str, location='args')

audit_search_args = reqparse.RequestParser()
audit_search_args.add_argument('source_ip', type=str, location='args')
audit_search_args.add_argument('resource_type', type=str, location='args')
audit_search_args.add_argument('resource_id', type=str, location='args')
audit_search_args.add_argument('operation', type=str, location='args')
audit_search_args.add_argument('status', type=str, location='args')
audit_search_args.add_argument('message', type=str, location='args')

audit_download_params = reqparse.RequestParser()
audit_download_params.add_argument('start_time', type=str, location='args')
audit_download_params.add_argument('end_time', type=str, location='args')
audit_download_params.add_argument('user', type=str, location='args', help="user name")
audit_download_params.add_argument('source_ip', type=str, location='args')
audit_download_params.add_argument('resource_type', type=str, location='args')
audit_download_params.add_argument('resource_id', type=str, location='args')
audit_download_params.add_argument('operation', type=str, location='args')
audit_download_params.add_argument('result', type=str, location='args')
audit_download_params.add_argument('message', type=str, location='args')


@ns.route('/')
class Audits(Resource):
    """Todo represent a resource in a RESTful app."""

    @ns.doc('list audit')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'audit list not found')
    @ns.expect(audit_list_args)
    @ns.marshal_list_with(audit_pagination_model)
    def get(self):
        """Get all audit items."""
        args = audit_list_args.parse_args()
        page = args.page
        per_page = args.per_page
        app.logger.debug("Get audit list's params are: {}".format(args))
        try:
            audits = get_audit_list(page, per_page, args)
            app.logger.info("Get audit list's result with page num {}, and length is {}".
                            format(audits.page, len(audits.items)))
        except ResourcesNotFoundError as e:
            app.logger.error("Audit list can\'t be found with params: page={}, per_page={}".
                             format(page, per_page))
            abort(404, e.message)
        return audits


@ns.route('/search')
class AuditSearch(Resource):
    @ns.doc('list risk_repository')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'audit list not found')
    @ns.expect(audit_search_args)
    @ns.marshal_list_with(audit_model)
    def get(self):
        """Get all audits items by search key"""
        args = audit_search_args.parse_args()
        app.logger.debug("Get audit search list's params are: {}".format(args))
        try:
            risks = audit_list_search(args)
            app.logger.info("Audit list's result, and result: {}".format(risks))
        except ResourcesNotFoundError as e:
            app.logger.error("Audit list can\'t be found with params: {}".
                             format(args))
            abort(404, e.message)
        return risks


@ns.route('/users')
class AuditUsers(Resource):
    @ns.doc('list audit users')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'audit list not found')
    @ns.marshal_list_with(audit_creator_model)
    def get(self):
        """Get all audits users list"""
        try:
            risks = get_audit_user_list()
            app.logger.info("Audit list's result, and result: {}".format(risks))
        except ResourcesNotFoundError as e:
            app.logger.error("Audit list can\'t be found")
            abort(404, e.message)
        return risks


@ns.route('/resources')
class AuditResources(Resource):
    @ns.doc('list audit users')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'audit list not found')
    @ns.marshal_list_with(audit_resource_model)
    def get(self):
        """Get all audits resources list"""
        try:
            resources = get_audit_resource_list()
            app.logger.info("Audit list's result, and result: {}".format(resources))
        except ResourcesNotFoundError as e:
            app.logger.error("Audit list can\'t be found.")
            abort(404, e.message)
        return resources


@ns.route('/download')
class AuditsDownload(Resource):
    """
    download audits to csv file
    """
    @ns.doc('download audits')
    @ns.expect(audit_download_params)
    @ns.response(404, 'no audits can be download')
    def get(self):
        """
        download audits according to the query conditions
        """
        args = audit_download_params.parse_args()
        app.logger.debug(u"Download audits with params: {}".format(args))
        time_now = datetime.now()
        try:
            app.logger.info(u"Download audits succeed")
            res = get_audits_csv(args)
            return Response(
                stream_with_context(res),
                mimetype="application/tar+gzip",
                headers={"Content-disposition": "attachment;filename=aops" + "_{}".format(time_now) + "_{}".format("audits.csv")})
        except ResourcesNotFoundError as e:
            app.logger.error(u"Download audits failed, reason: {}".format(e.msg))
            abort(404, e.msg)

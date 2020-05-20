# !/usr/bin/python
# -*- coding:utf-8 -*-

"""
@author: fengli
@time: 2018/8/11 下午1:44
@file: approval
"""

from flask import abort
from flask import current_app as app
from flask_restplus import Resource
from flask_restplus import reqparse
from flask_restplus import Model
from flask_restplus import fields
from flask_restplus.namespace import Namespace
from aops.applications.exceptions.exception import ValidationError
from aops.applications.exceptions.exception import ResourceNotFoundError
from aops.applications.handlers.v1.common import pagination_base_model
from aops.applications.database.apis.approval.approval import create_approval
from aops.applications.database.apis.approval.approval import get_approvals
from aops.applications.database.apis.approval.approval import update_approval_with_id
from aops.applications.database.apis.job.instant_job import approval_execution
from aops.applications.handlers.v1 import passport_auth


ns = Namespace('approvals', description='operation approval module')


approvals_model = Model('approvals_model', {
    'id': fields.Integer(required=True, description='approval id of the task'),
    'created_at': fields.DateTime(required=True, description='Resource create time point'),
    'operator': fields.String(required=True, description='task applying operator'),
    'operation_type': fields.String(required=True, description='task type'),
    'task_name': fields.String(required=True, description='name of the task'),
    'task_id': fields.Integer(required=True, description='task execute id of the task'),
    'tmp_id': fields.Integer(required=True, description='template id of the task'),
    'target': fields.String(required=True, description='target ip of the task'),
    'execute_time': fields.DateTime(required=True, description='execute time of the task'),
    'risk': fields.String(required=True, description='risk of the task'),
    'status': fields.String(required=True, description='status of the task'),
    'approver': fields.String(required=True, description='approver of the task'),
    'description': fields.String(required=True, description='description for the approval result')
})

approval_create_model = Model('approval_create_model', {
    'operator': fields.String(required=True, description='task applying operator'),
    'operation_type': fields.String(required=True, description='task type'),
    'task_name': fields.String(required=True, description='name of the task'),
    'task_id': fields.Integer(required=True, description='task execute id of the task'),
    'tmp_id': fields.Integer(required=True, description='template id of the task'),
    'target': fields.String(required=True, description='target ip of the task'),
    'execute_time': fields.DateTime(required=True, description='execute time of the task'),
    'risk': fields.String(required=True, description='risk of the task'),
    'status': fields.String(required=True, description='status of the task')
})

approval_pagination_model = pagination_base_model.clone("approval_pagination_model", {
    "items": fields.List(fields.Nested(approvals_model))
})

approval_update_model = Model('approval_update_model', {
    'status': fields.String(required=True, description='status of the task'),
    'approver': fields.String(required=True, description='approver of the task'),
    'description': fields.String(required=True, description='description for the approval result')
})

ns.add_model(approvals_model.name, approvals_model)
ns.add_model(approval_create_model.name, approval_create_model)
ns.add_model(approval_update_model.name, approval_update_model)
ns.add_model(approval_pagination_model.name, approval_pagination_model)

approval_query_params = reqparse.RequestParser()
approval_query_params.add_argument('start_time', type=str, location='args')
approval_query_params.add_argument('end_time', type=str, location='args')
approval_query_params.add_argument('operator', type=str, location='args')
approval_query_params.add_argument('operation_type', type=str, location='args')
approval_query_params.add_argument('task_name', type=str, location='args')
approval_query_params.add_argument('approver', type=str, location='args')
approval_query_params.add_argument('status', type=str, location='args')
approval_query_params.add_argument("page", type=int, location='args', required=True, help='Current page number.')
approval_query_params.add_argument("per_page", type=int, location='args', required=True, help='The number of items in a page.')


approval_create_params = reqparse.RequestParser()
approval_create_params.add_argument('operator', type=str)
approval_create_params.add_argument('operation_type', type=str)
approval_create_params.add_argument('task_name', type=str)
approval_create_params.add_argument('task_id', type=int)
approval_create_params.add_argument('target', type=str)
approval_create_params.add_argument('execute_time', type=str)
approval_create_params.add_argument('risk', type=str)
approval_create_params.add_argument('status', type=str)

approval_update_parser = reqparse.RequestParser()
approval_update_parser.add_argument('status', required=True, type=str)
approval_update_parser.add_argument('approver', required=True, type=str)
approval_update_parser.add_argument('description', required=True, type=str)


@ns.route('/')
class Approvals(Resource):

    """
    offering interface to query and create approval records
    """
    @ns.response(404, 'no approval records are founded')
    @ns.expect(approval_query_params)
    @ns.marshal_list_with(approval_pagination_model)
    def get(self):

        """
        query approval records
        """
        args = approval_query_params.parse_args()
        app.logger.debug(u'Query approvals with {}'.format(args))
        try:
            approvals = get_approvals(**args)
            app.logger.info(u'Query approvals succeed')
            return approvals, 200
        except ResourceNotFoundError as e:
            app.logger.error(u'Query approvals failed, reason: {}'.format(e.msg))
            abort(404, e.msg)

    @ns.response(401, 'create approval event failed')
    @ns.expect(approval_create_model)
    @ns.marshal_with(approvals_model)
    def post(self):

        """
        create new approval record here
        """
        args = approval_create_params.parse_args()
        app.logger.debug(u'Create approval record: {}'.format(args))
        try:
            approval = create_approval(**args)
            app.logger.info(u'Create approval succeed, approval id: {}'.format(approval.id))
            return approval, 201
        except ValidationError as e:
            app.logger.error(u'Create approval failed, reason: {}'.format(e.msg))
            abort(401, e.msg)


@ns.route('/<int:identifier>')
@ns.response(404, 'Approval not found')
@ns.param('identifier', 'The approval\'s identifier')
class Approval(Resource):

    @ns.expect(approval_update_model)
    @ns.marshal_with(approval_create_model)
    @passport_auth()
    def put(self, identifier):
        """
        update approval status
        """
        args = approval_update_parser.parse_args()
        app.logger.debug(u'Update approval {}, args: {}'.format(identifier, args))
        try:
            approval = update_approval_with_id(identifier, **args)
            if args.status == '2':
                approval_execution(approval.task_id)
            app.logger.info(u'Update approval succeed, id: {}'.format(identifier))
            return approval, 200
        except (ResourceNotFoundError, ValidationError) as e:
            app.logger.error(u'Update approval failed, reason: {}'.format(e.msg))
            abort(401, e.msg)


if __name__ == '__main__':
    pass

#!/usr/bin/env python
# -*- coding:utf-8 -*-
from flask_restplus import Resource, fields, Model, reqparse
from flask import abort, request, session, current_app as app
from aops.applications.handlers.v1.common import time_util, pagination_base_model
from aops.applications.database.apis.repository.file_review import get_file_review_list, get_file_review_with_id, \
    review_file_with_id, cancel_review_file_with_id
from aops.applications.exceptions.exception import Error, NotFoundError, ResourceNotFoundError, ResourcesNotFoundError

from aops.applications.handlers.v1.repository import ns
from aops.applications.handlers.v1.repository.repository import pagination_args, script_repository_model


file_review_model = time_util.clone('FileReview', {
    'id': fields.Integer(readOnly=True, description='The file\'s identifier'),
    'project_id': fields.Integer(readOnly=True, description='The file\'s project id'),
    'path': fields.String(readOnly=True, description='The file\'s path'),
    'type': fields.String(required=True, description='The file\'s type'),
    'comment': fields.String(required=True, description='The file\' risk statement'),
    'status': fields.String(required=True, description='The file\'s status'),
    'commit_sha': fields.String(description='The file\'s commit_sha'),
    'submitter': fields.String(required=True, description='The file\'s submitter'),
    'approver': fields.String(required=True),
    'approval_comments': fields.String(required=True),
    'target_branch': fields.String(required=True),
    'scripts': fields.List(fields.Nested(script_repository_model), description='file review\'s script list'),
    'risk_level': fields.Integer(required=True, description='The task\'s risk level'),
})


file_approve_model = Model('FileApprove', {
    'status': fields.String(required=True, description='The approve\'s status'),
    'risk_level': fields.Integer(required=False, description='The task\'s risk level'),
    'approval_comments': fields.String(required=False, description='The task\' risk statement'),
})


file_review_pagination_model = pagination_base_model.clone("TaskReviewPagination", {
    "items": fields.List(fields.Nested(file_review_model))
})

ns.add_model(file_review_model.name, file_review_model)
ns.add_model(file_approve_model.name, file_approve_model)
ns.add_model(file_review_pagination_model.name, file_review_pagination_model)


file_parser = reqparse.RequestParser()
file_parser.add_argument('status', type=str)

file_approve_parser = file_parser.copy()
file_approve_parser.add_argument('risk_level', type=int)
file_approve_parser.add_argument('approval_comments')

file_review_list_args = pagination_args.copy()
file_review_list_args.add_argument('type', type=str, location='args', choices=('scripts', 'applications',
                                                                               'configurations'))
file_review_list_args.add_argument('status', type=str, location='args', choices=('pass', 'not_pass', 'pending'))
file_review_list_args.add_argument('submitter', type=str, location='args')
file_review_list_args.add_argument('name', type=str, location='args')
file_review_list_args.add_argument('approver', type=str, location='args')


@ns.route('/review/')
class FileReviews(Resource):
    """
    Shows a list of all need review files , and lets you POST to review files
    """

    @ns.doc('list_all_need_review_files')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'file review list not found')
    @ns.marshal_list_with(file_review_pagination_model)
    @ns.expect(file_review_list_args)
    def get(self):
        """
        List all need review files
        Returns:
            all need review files
        """
        args = file_review_list_args.parse_args()
        page = args.page
        per_page = args.per_page
        name = args.name
        type = args.type
        status = args.status
        creator = args.submitter
        approver = args.approver
        fuzzy_query = args.fuzzy_query
        app.logger.debug("Get file review list's params are: {}".format(args))
        try:
            business_group = request.cookies.get('BussinessGroup')
            file_reviews = get_file_review_list(page, per_page, name=name, type=type,
                                                status=status, creator=creator, approver=approver,
                                                fuzzy_query=fuzzy_query, business_group=business_group)
            app.logger.info("Get file review list's result with page num {}, and length is {}".format(
                file_reviews.page, len(file_reviews.items)))
        except ResourcesNotFoundError as e:
            app.logger.error("file review list can\'t be found with params: page={}, per_page={}".format(page,
                                                                                                         per_page))
            abort(404, e.message)
        return file_reviews


@ns.route('/review/<int:identifier>')
@ns.response(404, 'file review not found')
@ns.param('identifier', 'The need review file\'s identifier')
class FileReview(Resource):
    """
    Shows a  need review files , and lets you POST to review file
    """

    @ns.doc('list_a_need_review_file')
    @ns.marshal_with(file_review_model)
    def get(self, identifier):
        """
        List a need review files
        Returns:
            a need review files
        """
        app.logger.debug("Get need review file item with id: {}".format(identifier))
        try:
            file_review = get_file_review_with_id(identifier)
            app.logger.info("Get need review file item with id {} 's result is: {}".format(identifier,
                                                                                           file_review.to_dict()))
        except NotFoundError as e:
            app.logger.error("file review item can\'t be found with id {}".format(identifier))
            abort(404, e.message)
        except Error as e:
            app.logger.error("Error occurred: {}".format(identifier, e.msg))
            abort(404, e.msg)
        return file_review

    @ns.doc('approval_file')
    @ns.expect(file_approve_model)
    @ns.marshal_with(file_review_model, code=200)
    def post(self, identifier):
        """
        Approve a file that requires approval
        Args:
            identifier: file id
        Returns:
            Just the file review item with this ID
        """
        review_info = file_approve_parser.parse_args()
        app.logger.debug("Review file item's params are: {}".format(review_info))
        try:
            user_info = session.get('user_info', {'user': 'admin'})
            creator = user_info.get('user')
            review_info.update(approver=creator)
            approve_file = review_file_with_id(identifier, review_info)
        except (NotFoundError, ResourceNotFoundError) as e:
            app.logger.error(e.msg)
            abort(e.code, e.msg)
        except Error as e:
            app.logger.error("file review item with id {}, Gitlab Error: {}".format(identifier, e.msg))
            abort(e.code, e.message)
        return approve_file

    @ns.doc('cancel file')
    @ns.marshal_with(file_review_model, code=200)
    def put(self, identifier):
        """
        Cancel a file approval
        Args:
            identifier: file id
        Returns:
            Just the file review item with this ID
        """
        app.logger.debug("Cancel review file item's id: {}".format(identifier))
        try:
            cancel_file = cancel_review_file_with_id(identifier)
        except (ResourceNotFoundError, NotFoundError) as e:
            app.logger.error(e.msg)
            abort(e.code, e.msg)
        except Error as e:
            app.logger.error("file review item with id {}, Gitlab Error: {}".format(identifier, e.msg))
            abort(e.code, e.message)
        return cancel_file

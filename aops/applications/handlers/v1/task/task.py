#!/usr/bin/env python
# -*- coding:utf-8 -*-
from flask import current_app
from flask_restplus import Namespace, Model, fields, reqparse, Resource, abort

from aops.applications.database.apis.task.task import get_tasks_list, create_task, get_task_with_id, \
    update_task_with_id, delete_tasks_with_ids, start_or_stop_tasks, get_creator_list, \
    generate_task_risk, get_tasks_list_with_enable
from aops.applications.database.apis.task.task_review import get_task_review_list, get_task_review_with_id, \
    approval_task, get_approver_list
from aops.applications.exceptions.exception import NotFoundError, ResourcesNotFoundError, \
    ResourcesNotDisabledError, ResourceNotFoundError, NoPermissionError, ConflictError, ApproveYourselfError, \
    ResourceAlreadyExistError
from aops.applications.handlers.v1.common import full_time_util, pagination_base_model
from aops.applications.handlers.v1 import passport_auth


ns = Namespace('/v1/tasks', description='Tasks operations')

"""task"""
task_without_id_model = Model('TaskWithoutID', {
    'name': fields.String(required=True, description='The task\'s name'),
    'type': fields.String(required=True, description='The task\'s type'),
    'language': fields.String(required=True, description='The task used language'),
    'target_system': fields.String(required=True, description='The task used system'),
    'description': fields.String(required=True, description='The task\'s description'),
    'script': fields.String(required=False, description='The task used scripts'),
    'time_out': fields.Integer(required=True, description='The task timeout limit'),
    'command': fields.String(required=False, description='The task used command'),
    'is_enable': fields.Boolean(required=True, default=0, description='Is this task enabled'),
    'script_parameter': fields.String(requitred=False, description='Is this task\'s task script parameter'),
    'script_version': fields.String(requitred=False, description='Is this task\'s task script version'),
    'file_selection': fields.String(required=False, description='The task file selection'),
    'target_directory': fields.String(required=False, description='The task target directory'),
    'file_owner': fields.String(required=False, description='The task file owner'),
    'file_permission': fields.String(required=False, description='The task file permission'),
    'is_replace': fields.Boolean(required=False, description='Is this task replace'),
    'risk_level': fields.Integer(required=True, description='The task\'s risk level'),
    'risk_statement': fields.String(required=True, description='The task\' risk statement'),
    'project_id': fields.String(),
    'change_result': fields.String(required=False),
})

task_model = task_without_id_model.clone('Task', full_time_util, {
    'id': fields.Integer(readOnly=True, description='The task\'s identifier'),
    'status': fields.String(required=True, description='The task\'s status'),
    'approver': fields.String(required=False, description='The task\'s approver'),
    'creator': fields.String(required=True, description='The task\'s creator'),
})

task_ids_model = Model('TaskIds', {
    'task_ids': fields.List(fields.Integer, description='Multiple id of tasks')
})

task_ids_operate_model = task_ids_model.clone('TaskIdsOperate', {
    'is_enable': fields.Boolean(required=True, description='Is this task enabled')
})

task_pagination_model = pagination_base_model.clone("TaskPagination", {
    "items": fields.List(fields.Nested(task_model))
})

creator_model = Model('TaskCreator', {
    'creator': fields.List(fields.String)
})

approver_model = Model('TaskApprover', {
    'approver': fields.List(fields.String)
})

task_risk_model = Model('TaskRisk', {
    'risk_level': fields.String(required=True, description='The task\'s risk level'),
    'risk_statement': fields.String(required=True, description='The task\' risk statement'),
})

command_model = Model('TaskCommand', {
    'command': fields.String(required=False, description='The task used command'),

})

ns.add_model(task_without_id_model.name, task_without_id_model)
ns.add_model(task_model.name, task_model)
ns.add_model(task_ids_model.name, task_ids_model)
ns.add_model(task_ids_operate_model.name, task_ids_operate_model)
ns.add_model(task_pagination_model.name, task_pagination_model)
ns.add_model(creator_model.name, creator_model)
ns.add_model(approver_model.name, approver_model)
ns.add_model(task_risk_model.name, task_risk_model)
ns.add_model(command_model.name, command_model)

task_without_id_parser = reqparse.RequestParser()
task_without_id_parser.add_argument('name')
task_without_id_parser.add_argument('type')
task_without_id_parser.add_argument('language')
task_without_id_parser.add_argument('target_system')
task_without_id_parser.add_argument('description')
task_without_id_parser.add_argument('script')
task_without_id_parser.add_argument('script_version')
task_without_id_parser.add_argument('time_out')
task_without_id_parser.add_argument('command')
task_without_id_parser.add_argument('is_enable', type=int)
task_without_id_parser.add_argument('script_parameter')
task_without_id_parser.add_argument('file_selection')
task_without_id_parser.add_argument('target_directory')
task_without_id_parser.add_argument('file_owner')
task_without_id_parser.add_argument('file_permission')
task_without_id_parser.add_argument('is_replace', type=int)
task_without_id_parser.add_argument('risk_level', type=int)
task_without_id_parser.add_argument('project_id', type=str)
task_without_id_parser.add_argument('risk_statement', type=unicode)

task_parser = task_without_id_parser.copy()
task_parser.add_argument('id', type=int)


task_ids_parser = reqparse.RequestParser()
task_ids_parser.add_argument('task_ids', type=list, location='json')

task_ids_operate_parser = task_ids_parser.copy()
task_ids_operate_parser.add_argument('is_enable', type=int)

command_parser = reqparse.RequestParser()
command_parser.add_argument('command')

task_list_args = reqparse.RequestParser()
task_list_args.add_argument('page', type=int, location='args', required=True, help='Current page number.')
task_list_args.add_argument("per_page", type=int, location='args', required=True, help='The number of items in a page.')
task_list_args.add_argument('name', type=unicode, location='args')
task_list_args.add_argument('type', location='args', choices=('command', 'script', 'file', 'playbook', ''))
task_list_args.add_argument('language', location='args')
task_list_args.add_argument('target_system', location='args')
task_list_args.add_argument('risk_level', location='args', choices=('1', '2', '3', ''))
task_list_args.add_argument('is_enable', location='args', choices=('1', '0', ''))
task_list_args.add_argument('creator', type=unicode, location='args')
task_list_args.add_argument('fq', location='args', dest="fuzzy_query")
"""end task"""

"""task review"""
review_record = Model('ReviewRecord', {
    'id': fields.Integer(readOnly=True),
    'risk_level': fields.String(required=True, description='The task\'s risk level'),
    'approver': fields.String(required=True),
    'status': fields.String(required=True),
    'updated_at': fields.String,
    'target_id': fields.Integer,
    'approval_comments': fields.String(required=False, description='The task\' risk statement'),
})

task_review_model = task_without_id_model.clone('TaskReview', full_time_util, {
    'id': fields.Integer(readOnly=True, description='The task\'s identifier'),
    'status': fields.String(required=True, description='The task\'s status'),
    'creator': fields.String(required=True, description='The task\'s creator'),
    'approval_comments': fields.String(),
    'approve_record': fields.List(fields.Nested(review_record))
})

task_approve_model = Model('TaskApprove', {
    'status': fields.String(required=True, description='The approve\'s status'),
    'risk_level': fields.Integer(required=False, description='The task\'s risk level'),
    'risk_statement': fields.String(required=False, description='The task\' risk statement'),
    'approval_comments': fields.String(required=False, description='The task\' risk statement'),
})

task_review_pagination_model = pagination_base_model.clone("TaskReviewPagination",{
    "items": fields.List(fields.Nested(task_review_model))
})

ns.add_model(review_record.name, review_record)
ns.add_model(task_review_model.name, task_review_model)
ns.add_model(task_approve_model.name, task_approve_model)
ns.add_model(task_review_pagination_model.name, task_review_pagination_model)

task_approve_parser = reqparse.RequestParser()
task_approve_parser.add_argument('status', type=str)
task_approve_parser.add_argument('risk_level', type=int)
task_approve_parser.add_argument('risk_statement')
task_approve_parser.add_argument('approval_comments')

task_review_list_args = reqparse.RequestParser()
task_review_list_args.add_argument('page', type=int, location='args', required=True, help='Current page number.')
task_review_list_args.add_argument("per_page", type=int, location='args', required=True, help='The number of items in a page.')
task_review_list_args.add_argument('name', location='args')
task_review_list_args.add_argument('type', location='args', choices=('command', 'script', 'file', 'playbook', ''))
task_review_list_args.add_argument('risk_level', location='args', choices=('1', '2', '3', ''))
task_review_list_args.add_argument('status', location='args', choices=('pass', 'no-pass', 'pending', ''))
task_review_list_args.add_argument('creator', location='args')
task_review_list_args.add_argument('approver', location='args')
task_review_list_args.add_argument('start_time', location='args')
task_review_list_args.add_argument('end_time', location='args')
task_review_list_args.add_argument('fq', location='args', dest="fuzzy_query")

"""end task review"""

""" script task """
script_task_model = task_without_id_model.clone('ScriptTask', full_time_util, {
    'id': fields.Integer(readOnly=True, description='The task\'s identifier'),
    'creator': fields.String(required=True, description='The task\'s creator'),
    'current_version': fields.String(required=True, description='The task\'s script current version'),
    'new_version': fields.String(required=True, description='The task\'s script new version'),
})

script_task_pagination_model = pagination_base_model.clone("ScriptTaskPagination", {
    "items": fields.List(fields.Nested(script_task_model))
})

ns.add_model(script_task_model.name, script_task_model)
ns.add_model(script_task_pagination_model.name, script_task_pagination_model)

"""end script task"""


@ns.route('/')
class Tasks(Resource):
    """
    Shows a list of all tasks, and lets you POST to add new tasks
    """

    @ns.doc('list_all_tasks')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'Task list not found')
    @ns.marshal_list_with(task_pagination_model)
    @ns.expect(task_list_args)
    # @passport_auth()
    def get(self):
        """
        list all tasks
        Returns:
            all tasks
        """
        args = task_list_args.parse_args()
        page = args.page
        per_page = args.per_page
        name = args.name
        type = args.type
        language = args.language
        target_system = args.target_system
        risk_level = args.risk_level
        is_enable = args.is_enable
        creator = args.creator
        fuzzy_query = args.fuzzy_query
        current_app.logger.debug("Get task list's params are: {}".format(args))
        try:
            tasks = get_tasks_list(page, per_page, name=name, type=type, language=language, target_system=target_system, risk_level=risk_level, is_enable=is_enable, creator=creator, fuzzy_query=fuzzy_query)
            current_app.logger.info("Get task list's result with page num {}, and length is {}".format(tasks.page, len(tasks.items)))
        except ResourcesNotFoundError as e:
            current_app.logger.error("Task list can\'t be found with params: page={}, per_page={}".format(page, per_page))
            abort(404, e.message)
        return tasks

    @ns.doc('create_task')
    @ns.expect(task_without_id_model)
    @ns.marshal_with(task_model, code=201)
    @passport_auth()
    def post(self):
        """
        create a task items
        Returns:
            the new task items
        """
        args = task_parser.parse_args()
        current_app.logger.debug("Create task item's params are: {}".format(args))
        try:
            created_task = create_task(args)
        except ResourceAlreadyExistError as e:
            current_app.logger.error(e.message)
            abort(409, e.message)
        current_app.logger.info("Created task item's result is: {}".format(created_task))
        return created_task, 201

    @ns.doc('delete_tasks')
    @ns.expect(task_ids_model)
    @ns.marshal_with(task_model, code=201)
    @passport_auth()
    def delete(self):
        """
        Delete multiple tasks
        Returns:
            The deleted tasks
        """
        args = task_ids_parser.parse_args()
        current_app.logger.debug("Delete task item with task ids: {}".format(args.task_ids))
        try:
            result = delete_tasks_with_ids(args)
        except ResourceNotFoundError as e:
            current_app.logger.error('task not found')
            abort(404, e.message)
        except ResourcesNotDisabledError as e:
            current_app.logger.error('This task no stop')
            abort(409, e.message)
        return result

    @ns.doc('start_or_stop_tasks')
    @ns.expect(task_ids_operate_model)
    @ns.marshal_with(task_model, code=200)
    @passport_auth()
    def put(self):
        """
        Start or stop multiple tasks
        Returns:
           The Operational task
        """
        args = task_ids_operate_parser.parse_args()
        current_app.logger.debug("Put task item with task ids: {}".format(args.task_ids))
        try:
            result = start_or_stop_tasks(args)
        except ResourceNotFoundError as e:
            current_app.logger.error('task not found')
            abort(404, e.message)
        except ConflictError as e:
            current_app.logger.error('This task is used by job')
            abort(404, e.message)
        current_app.logger.info("Put task item with task ids {}".format(args.task_ids))
        return result


@ns.route('/<int:identifier>')
@ns.response(404, 'Task not found')
@ns.param('identifier', 'The Task\'s identifier')
class Task(Resource):
    """Show a single task item and lets you delete them"""

    @ns.doc('get_task')
    @ns.marshal_with(task_model)
    @ns.response(200, 'Get single task item', model=task_model)
    # @passport_auth()
    def get(self, identifier):
        """
        Fetch a given task with identifier.
        Args:
            identifier: task id

        Returns:
            Get the task item with id.
        """
        current_app.logger.debug("Get task item with id: {}".format(identifier))
        try:
            task = get_task_with_id(identifier)
            current_app.logger.info("Get task item with id {} 's result is: {}".format(identifier, task.to_dict()))
        except ResourceNotFoundError as e:
            current_app.logger.error("Task item can\'t be found with id {}".format(identifier))
            abort(404, e.message)
        return task

    @ns.expect(task_without_id_model)
    @ns.response(200, 'task updated')
    @ns.marshal_with(task_model)
    @passport_auth()
    def put(self, identifier):
        """Update a task given its identifier"""

        task_info = task_without_id_parser.parse_args()
        current_app.logger.debug("Update task item's params are: {}".format(task_info))
        try:
            result = update_task_with_id(identifier, task_info)
        except ResourceNotFoundError as e:
            current_app.logger.error("Task item can\'t be found with id {}".format(identifier))
            abort(404, e.message)
        except NoPermissionError as e:
            current_app.logger.error("no permission to change this task {}".format(identifier))
            abort(404, e.message)
        except ConflictError as e:
            current_app.logger.error("This resource has other resources to reuse {}".format(identifier))
            abort(404, e.message)

        if result == 409:
            current_app.logger.error("No permission or pending approval for task with {}".format(identifier))
            abort(409, 'No permission or pending approval')
        current_app.logger.info("Update task item's result is: {}".format(result))
        return result, 200

@ns.route('/task-creator/')
class TaskCreator(Resource):
    """
    Screening task
    """
    @ns.doc('list_creator')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'Task creator list not found')
    @ns.marshal_list_with(creator_model)
    def get(self):
        """Get all task creator"""
        try:
            creator = get_creator_list()
            current_app.logger.info("Get task creator list's result with {}".format(creator))
        except ResourcesNotFoundError as e:
            current_app.logger.error("Task creator list can\'t be found ")
            abort(404, e.message)
        return creator

@ns.route('/task-approver/')
class TaskApprover(Resource):
    """
    Screening task
    """
    @ns.doc('list_approver')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'Task approver list not found')
    @ns.marshal_list_with(approver_model)
    def get(self):
        """Get all task approver"""
        try:
            approver= get_approver_list()
            current_app.logger.info("Get task approver list's result with {}".format(approver))
        except ResourcesNotFoundError as e:
            current_app.logger.error("Task approver list can\'t be found ")
            abort(404, e.message)
        return approver


@ns.route('/task-risk/')
class TaskRisk(Resource):
    """
    Get task risk
    """
    @ns.doc('generate_task_risk')
    @ns.expect(command_model)
    @ns.marshal_with(task_risk_model, code=200)
    def post(self):
        """
        generate task risk
        Returns:
            Task risk
        """
        args = command_parser.parse_args()
        current_app.logger.debug("task risk item's params are: {}".format(args))
        result = generate_task_risk(args)
        current_app.logger.info("task risk item's result is: {}".format(result))
        return result


@ns.route('/review/')
class TaskReviews(Resource):
    """
    Shows a list of all need review tasks , and lets you POST to review tasks
    """

    @ns.doc('list_all_need_review_tasks')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'Task review list not found')
    @ns.marshal_list_with(task_review_pagination_model)
    @ns.expect(task_review_list_args)
    def get(self):
        """
        List all need review tasks
        Returns:
            all need review tasks
        """
        args = task_review_list_args.parse_args()
        page = args.page
        per_page = args.per_page
        name = args.name
        type = args.type
        risk_level = args.risk_level
        status = args.status
        creator = args.creator
        approver = args.approver
        start_time = args.start_time
        end_time = args.end_time
        fuzzy_query = args.fuzzy_query
        current_app.logger.debug("Get task review list's params are: {}".format(args))
        try:
            task_reviews = get_task_review_list(page, per_page, name=name, type=type, risk_level=risk_level,
                                                status=status, creator=creator, approver=approver, start_time=start_time,
                                                end_time=end_time, fuzzy_query=fuzzy_query)
            current_app.logger.info("Get task review list's result with page num {}, and length is {}"
                                    .format(task_reviews.page, len(task_reviews.items)))
        except ResourcesNotFoundError as e:
            current_app.logger.error("Task review list can\'t be found with params: page={}, per_page={}"
                                     .format(page, per_page))
            abort(404, e.message)
        return task_reviews


@ns.route('/review/<int:identifier>')
@ns.response(404, 'task review not found')
@ns.param('identifier', 'The need review task\'s identifier')
class TaskReview(Resource):
    """
    Shows a  need review tasks , and lets you POST to review task
    """

    @ns.doc('list_a_need_review_task')
    @ns.marshal_list_with(task_review_model)
    def get(self, identifier):
        """
        List a need review tasks
        Returns:
            a need review tasks
        """
        current_app.logger.debug("Get need review task item with id: {}".format(identifier))
        try:
            task_review = get_task_review_with_id(identifier)
            current_app.logger.info("Get need review task item with id {} 's result is: {}"
                                    .format(identifier, task_review.to_dict()))
        except NotFoundError as e:
            current_app.logger.error("Task review item can\'t be found with id {}".format(identifier))
            abort(404, e.message)
        return task_review

    @ns.doc('approval_task')
    @ns.expect(task_approve_model)
    @ns.marshal_with(task_review_model, code=201)
    @passport_auth()
    def post(self, identifier):
        """
        Approve a task that requires approval
        Args:
            identifier: task id
        Returns:
            Just the task review item with this ID
        """
        current_app.logger.debug("Get need review task item with id: {}".format(identifier))
        args = task_approve_parser.parse_args()
        current_app.logger.debug("Review task item's params are: {}".format(args))
        try:
            approve_task = approval_task(identifier, args)
            current_app.logger.info("Get need review task item with id {} 's result is: {}"
                                    .format(identifier, approve_task.to_dict()))
        except ResourceNotFoundError as e:
            current_app.logger.error("Task review item can\'t be found with id {}".format(identifier))
            abort(404, u'该任务对象查询不到')
        except ConflictError as e:
            current_app.logger.error("Reviewed for review task with {}".format(identifier))
            abort(404, u'该任务已经审批过,无需重复审批')
        except ApproveYourselfError as e:
            current_app.logger.error("Cannot approve tasks created by yourself")
            abort(404, u'不能审批你自己创建的任务')
        current_app.logger.info("Review task item's result is: {}".format(approve_task))
        return approve_task


@ns.route('/enable/')
class EnableTasks(Resource):
    """
    Shows a list of all enable tasks, and lets you POST to add new tasks
    """

    @ns.doc('list_all_enable_tasks')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'Task list not found')
    @ns.marshal_list_with(task_pagination_model)
    @ns.expect(task_list_args)
    # @passport_auth()
    def get(self):
        """
        list all enable tasks
        Returns:
            all tasks
        """
        args = task_list_args.parse_args()
        page = args.page
        per_page = args.per_page
        type = args.type
        target_system = args.target_system
        name = args.name
        current_app.logger.debug("Get task list's params are: {}".format(args))
        try:
            tasks = get_tasks_list_with_enable(page, per_page, type=type, target_system=target_system, name=name)
            current_app.logger.info("Get task list's result with page num {}, and length is {}"
                                    .format(tasks.page, len(tasks.items)))
        except ResourcesNotFoundError as e:
            current_app.logger.error("Task list can\'t be found with params: page={}, per_page={}".format(page, per_page))
            abort(404, e.message)
        return tasks



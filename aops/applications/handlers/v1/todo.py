#!/usr/bin/env python
# -*- coding:utf-8 -*-
import gevent
import gevent.time as gtime

from flask import current_app as app
from flask_restplus import Namespace, Resource, fields, reqparse, Model
from flask_restplus.errors import abort

from aops.applications.database.apis.todo import get_todo_list, create_todo, get_todo_with_id, \
    delete_todo_with_id, update_todo_with_id
from aops.applications.exceptions.exception import ResourceNotFoundError, ResourcesNotFoundError, \
    ResourceAlreadyExistError
from aops.applications.handlers.v1.common import time_util, pagination_base_model
from aops.applications.handlers.v1 import passport_auth, only_audit_log

ns = Namespace('/v1/todos', description='TODO operations')

todo_without_id_model = Model('TodoWithoutId', {
    'name': fields.String(required=True, description='The todo\'s name'),
    'nickname': fields.String(required=True, description='The todo\'s nickname'),
    'age': fields.Integer(required=True, description='The todo\'s age'),
    'email': fields.String(required=False, description='The todo\'s email')
})

todo_model = todo_without_id_model.clone("Todo", time_util, {
    'id': fields.Integer(readOnly=True, description='The todo\'s identifier')
})

todo_pagination_model = pagination_base_model.clone("TodoPagination", {
    "items": fields.List(fields.Nested(todo_model))
})

ns.add_model(todo_without_id_model.name, todo_without_id_model)
ns.add_model(todo_model.name, todo_model)
ns.add_model(todo_pagination_model.name, todo_pagination_model)

todo_without_id_parser = reqparse.RequestParser()
todo_without_id_parser.add_argument('name', type=unicode)
todo_without_id_parser.add_argument('nickname', type=unicode)
todo_without_id_parser.add_argument('age', type=int)
todo_without_id_parser.add_argument('email', type=unicode)

todo_parser = todo_without_id_parser.copy()
todo_parser.add_argument('id', type=int)

todo_list_args = reqparse.RequestParser()
todo_list_args.add_argument("page", type=int, location='args', required=True, help='Current page number.')
todo_list_args.add_argument("per_page", type=int, location='args', required=True, help='The number of items in a page.')
todo_list_args.add_argument("nickname", type=unicode, location='args')
todo_list_args.add_argument("name", type=unicode, location='args')
todo_list_args.add_argument("fq", type=unicode, location='args', dest="fuzzy_query")


@ns.route('/')
class Todos(Resource):
    """Todo represent a resource in a RESTful app."""

    @ns.doc('list_todos')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'Todo list not found')
    @ns.expect(todo_list_args)
    @ns.marshal_list_with(todo_pagination_model)
    # @passport_auth()
    def get(self):
        """Get all todo items."""
        args = todo_list_args.parse_args()
        page = args.page
        per_page = args.per_page
        fq = args.fuzzy_query
        name = args.name
        nickname = args.nickname
        app.logger.debug(u"Get todo list's params are: {}".format(args))
        try:
            todos = get_todo_list(page, per_page, fuzzy_query=fq, nickname=nickname, name=name)
            app.logger.info(u"Get todo list's result with page num {}, and length is {}".
                            format(todos.page, len(todos.items)))
        except ResourcesNotFoundError as e:
            app.logger.error(u"Todo list can\'t be found with params: page={}, per_page={}".
                             format(page, per_page))
            abort(404, e.message)
        return todos

    @ns.doc('create_todo')
    @ns.expect(todo_without_id_model)
    @ns.marshal_with(todo_model, code=201)
    def post(self):
        """Create a todo items."""
        args = todo_parser.parse_args()
        app.logger.debug(u"Create todo item's params are: {}".format(args))
        try:
            created_todo = create_todo(args)
            app.logger.info(u"Created todo item's result is: {}".format(created_todo))
        except ResourceAlreadyExistError as e:
            app.logger.error(e.message)
            abort(409, e.message)
        return created_todo, 201


def _wait_to_do_nothing(app):
    app.logger.debug(u"_wait_to_do_nothing will sleep 3 second")
    gtime.sleep(3)
    app.logger.debug(u"_wait_to_do_nothing Finished!!!")


@ns.route('/<int:identifier>')
@ns.response(404, 'Todo not found')
@ns.param('identifier', 'The todo\'s identifier')
class Todo(Resource):
    """Show a single todo item and lets you update and delete them."""

    @ns.doc('get_todo')
    @ns.marshal_with(todo_model)
    @ns.response(200, 'Get single todo item', model=todo_model)
    @only_audit_log(username='god')
    def get(self, identifier):
        """Fetch a given todo with identifier."""
        app.logger.debug(u"Get todo item with id: {}".format(identifier))
        try:
            todo = get_todo_with_id(identifier)
            app.logger.info(u"Get todo item with id {} 's result is: {}".format(identifier, todo.to_dict()))
        except ResourceNotFoundError as e:
            app.logger.error(e.message)
            abort(404, e.message)

        g = gevent.spawn(_wait_to_do_nothing, app._get_current_object())
        g.start()
        return todo

    @ns.doc('delete_todo')
    @ns.response(200, 'Todo deleted', model=todo_model)
    @ns.marshal_with(todo_model)
    @only_audit_log(username='input custom user', notes="input custom message")
    def delete(self, identifier):
        """Delete a todo given its identifier."""
        app.logger.debug(u"Delete todo item with id: {}".format(identifier))
        try:
            todo = get_todo_with_id(identifier)
            app.logger.info(u"Delete todo item with id {},the todo info is: {}".format(identifier, todo.to_dict()))
        except ResourceNotFoundError as e:
            app.logger.error(u"Todo item can\'t be found with id {}".format(identifier))
            abort(404, e.message)
        delete_todo_with_id(identifier)
        return todo, 200

    @ns.expect(todo_without_id_model)
    @ns.response(200, 'Todo updated', model=todo_model)
    @ns.marshal_with(todo_model)
    def put(self, identifier):
        """Update a todo given its identifier."""
        todo_info = todo_without_id_parser.parse_args()
        app.logger.debug(u"Update todo item with id: {}, and info is: {}".format(identifier, todo_info))
        try:
            get_todo_with_id(identifier)
            app.logger.info(u"Update todo item with id {},and latest info is: {}".format(identifier, todo.to_dict()))
        except ResourceNotFoundError as e:
            app.logger.error(u"Todo item can\'t be found with id {}".format(identifier))
            abort(404, e.message)
        todo = update_todo_with_id(identifier, todo_info)
        return todo, 200

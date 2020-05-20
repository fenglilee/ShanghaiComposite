#!/usr/bin/env python
# -*- coding:utf-8 -*-
import datetime

from sqlalchemy import desc
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.exceptions import NotFound

from aops.applications.database.models.todo import Todo
from aops.applications.exceptions.exception import ResourceNotFoundError, ResourcesNotFoundError, \
    ResourceAlreadyExistError, ValidationError


def get_todo_list(page, per_page, name=None, nickname=None, fuzzy_query=None):
    """Get all todo items

    Returns:
        Todo items list.
    """

    # desc order by update_time is default option
    q = Todo.query.filter_by(is_deleted=False). \
        order_by(desc(Todo.updated_at))

    # Precise query example
    if nickname:
        q = q.filter(Todo.nickname.like(u"%{}%".format(nickname)))
    if name:
        q = q.filter(Todo.name.like(u"%{}%".format(name)))

    # Fuzzy query example
    if fuzzy_query:
        q = q.filter(Todo.name.concat(Todo.email).concat(Todo.nickname).like(u"%{}%".format(fuzzy_query)))

    # return pagination body
    try:
        return q.paginate(page=page, per_page=per_page)
    except NotFound:
        raise ResourcesNotFoundError("TODO")


def create_todo(args):
    """Create a todo item with args

    Args:
        args: dict which contain name, age, email

    Returns:
        Just the create todo item.
    """
    try:
        todo = Todo.create(name=args.name, age=args.age, email=args.email, nickname=args.nickname)
    except ValidationError:
        raise ResourceAlreadyExistError("Todo")
    return todo.to_dict()


def get_todo_with_id(identifier):
    """Get a todo item with identifier

    Args:
        identifier(int): ID for todo item

    Returns:
        Just the todo item with this ID.

    Raises:
        NotFoundError: Todo item is not found
    """
    try:
        todo = Todo.query.filter_by(id=identifier, is_deleted=False).one()
    except NoResultFound:
        raise ResourceNotFoundError('Todo', identifier)

    return todo


def delete_todo_with_id(identifier):
    """Delete a todo item with identifier

    Args:
        identifier(int): ID for todo item

    Returns:
        None
    """
    Todo.soft_delete_by(id=identifier)


def update_todo_with_id(identifier, todo_info):
    """Update a todo item with identifier

    Args:
        identifier(int): ID for todo item
        todo_info: update todo with this info

    Returns:
        Just the todo item with this ID.

    Raises:
        NotFoundError: Todo item is not found
    """
    todo_info.update(
        id=identifier,
        updated_at=datetime.datetime.now()
    )
    todo = Todo.query.filter_by(id=identifier, is_deleted=False).first()
    if todo is None:
        raise ResourceNotFoundError('Todo', identifier)
    return todo.update(**todo_info)

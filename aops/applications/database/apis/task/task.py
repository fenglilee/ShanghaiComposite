#!/usr/bin/env python
# -*- coding:utf-8 -*-

from datetime import datetime

from flask import request, session
from sqlalchemy import or_
from sqlalchemy.orm.exc import NoResultFound

from aops.applications.database.models import SysConfigApprove
from aops.applications.database.models.repository.risk_command import RiskRepository
from aops.applications.database.models.task.task import Task,TaskReview
from aops.applications.exceptions.exception import  ResourcesNotFoundError, \
    ResourceAlreadyExistError, ResourcesNotDisabledError, ResourceNotFoundError, \
    NoPermissionError, ConflictError


def get_tasks_list(page, per_page, name=None, type=None, language=None, target_system=None, risk_level=None, is_enable=None, creator=None, fuzzy_query=None):
    """
    Get all tasks
    Returns:
        task list
    """
    business_group = request.cookies.get('BussinessGroup')

    q = Task.query.filter_by(is_deleted=False, business_group=business_group).order_by(Task.updated_at.desc())

    if creator:
        q = q.filter(Task.creator.like(u"%{}%".format(creator)))

    if type:
        q = q.filter(Task.type.like(u"%{}%".format(type)))

    if language:
        q = q.filter(Task.language.like(u"%{}%".format(language)))

    if target_system:
        q = q.filter(Task.target_system.like(u"%{}%".format(target_system)))

    if risk_level:
        q = q.filter(Task.risk_level.like(u"%{}%".format(risk_level)))

    if is_enable:
        q = q.filter(Task.is_enable.like(u"%{}%".format(is_enable)))

    if name:
        q = q.filter(Task.name.like(u"%{}%".format(name)))

    if fuzzy_query:
        q = q.filter(Task.name.concat(Task.name).concat(Task.type).concat(Task.language).concat(Task.task_system).concat(Task.is_enable).concat(Task.risk_level).concat(Task.creator).concat(Task.fuzzy_query).like(u"%{}%".format(fuzzy_query)))

    try:
        return q.paginate(page=page, per_page=per_page)
    except Exception as e:
        raise ResourcesNotFoundError("TASK")

def get_tasks_list_with_enable(page, per_page, type=None, target_system=None, name=None):
    """
    Get all enable tasks
    Returns:
        task list
    """
    business_group = request.cookies.get('BussinessGroup')

    q = Task.query.filter_by(is_deleted=False, is_enable=True, business_group=business_group).order_by(Task.updated_at.desc())
    q = q.filter(or_(Task.status == u'无需审批', Task.status == u'审批通过'))

    if type:
        q = q.filter(Task.type.like(u"%{}%".format(type)))

    if target_system:
        q = q.filter(Task.target_system.like(u"%{}%".format(target_system)))

    if name:
        q = q.filter(Task.name.like(u"%{}%".format(name)))

    try:
        return q.paginate(page=page, per_page=per_page)
    except Exception as e:
        raise ResourcesNotFoundError("TASK")

def get_creator_list():
    """
    Get all task creator
    Returns:
        all task creator
    """
    business_group = request.cookies.get('BussinessGroup')

    q = Task.query.filter_by(is_deleted=False, business_group=business_group).all()
    if q:
        return {'creator': set([task.creator for task in q])}
    return {}

def _generate_risk(command, args):
    if command.name in args.command:
        return command

def generate_task_risk(args):
    """
    Generate task risk
    Args:
        args: This task content

    Returns:
        task risk and task risk statement
    """
    risk_repository_list = RiskRepository.query.filter_by(is_deleted=False).all()
    if risk_repository_list:
        risk_command = [_generate_risk(command, args) for command in risk_repository_list if _generate_risk(command, args)]
        if not risk_command:
            risk_level = 3
            risk_statement = u'没有匹配到任何风险命令'
        else:
            risk_level_list = [command.risk_level for command in risk_command]
            risk_statement_list = [command.comment for command in risk_command]
            risk_level = max(map(int, risk_level_list))
            risk_statement = ','.join(risk_statement_list)
    else:
        risk_level = 3
        risk_statement = u'风险命令库为空'
    return {'risk_level': risk_level, 'risk_statement': risk_statement}

def _create(object, data):
    try:
        task = object.create(**data)
    except Exception:
        raise ResourceAlreadyExistError("{}".format(object.__name__))
    return task

def get_level():
    sys_config_approve = SysConfigApprove.query.filter_by(is_deleted=False, script_on=True).first()
    if sys_config_approve:
        return sys_config_approve.level
    return -1

def create_task(args):
    """
    Create a task with args
    Args:
        args:dict which contain (name,name,type,language,target_syste,description,
        script,script_version,risk_level,status,approver,command,creator,is_enable)

    Returns:
        the created task
    """
    business_group = request.cookies.get('BussinessGroup')
    creator = session.get('user_info').get('user')

    data = {
        'name': args.name,
        'type': args.type,
        'language': args.language,
        'target_system': args.target_system,
        'description': args.description,
        'script_version': args.script_version,
        'script_parameter': args.script_parameter,
        'time_out': args.time_out,
        'is_enable': args.is_enable,
        'creator': creator,
        'command': args.command,
        'risk_level': args.risk_level,
        'script': args.script,
        'risk_statement': args.risk_statement,
        'file_selection': args.file_selection,
        'target_directory': args.target_directory,
        'file_owner': args.file_owner,
        'file_permission': args.file_permission,
        'is_replace': args.is_replace,
        'project_id': args.project_id,
        'business_group': business_group,
    }

    level = get_level()
    if int(args.risk_level) >= int(level):
        data.update(status=u'审批中')
        task = _create(Task, data)
        data.update(task_id=task.id)
        task_review = _create(TaskReview, data)
        return task_review
    else:
        data.update(status=u'无需审批')
        task = _create(Task, data)
        return task

def get_task_with_id(identifier):
    """
    Get a task with identifier
    Args:
        identifier: ID for task item

    Returns:
        Just the task item with this ID

    Raises:
          NotFoundError: task is not found
    """
    try:
        task = Task.query.filter_by(id=identifier, is_deleted=False).one()
    except Exception:
        raise ResourceNotFoundError('Task', identifier)
    return task

def job_get_task(identifier):
    """
    Get a task with identifier
    Args:
        identifier: ID for task item

    Returns:
        Just the task item with this ID

    Raises:
          NotFoundError: task is not found
    """
    try:
        task = Task.query.filter_by(id=identifier, is_deleted=False, is_enable=True).one()
    except NoResultFound:
        raise ResourceNotFoundError('Task', identifier)
    return task

def _delete_task_with_id(identifier, deleted_task_list):
    task = get_task_with_id(identifier)
    if task.is_enable == False:
        task.name = task.name + '-' + str(datetime.now())
        Task.soft_delete_by(id=identifier)
        deleted_task_list.append(task)
        task_review = TaskReview.query.filter_by(task_id=task.id, is_deleted=False).first()
        if task_review and task_review.status == u'审批中':
            task_review.update(is_deleted=True)
        return task
    raise ResourcesNotDisabledError('Task', identifier)

def delete_tasks_with_ids(args):
    """
    Delete task with task_ids
    Args:
        task_ids: ID for task item

    Returns:
        Just the task items with this task_ids.
    """
    deleted_task_list = []
    for task_id in args.task_ids:
        _delete_task_with_id(task_id,  deleted_task_list)
    return deleted_task_list

def update_task_with_id(identifier, task_info):
    """
    Update a task with identifier
    Args:
        identifier: ID for task item
        task_info: update task with this info

    Returns:
        Just the task item with this ID.
    """
    business_group = request.cookies.get('BussinessGroup')
    login_name = session.get('user_info').get('user')

    task_info.update(creator=login_name, updated_at=datetime.now(), business_group=business_group)
    task = get_task_with_id(identifier)
    if task.creator != login_name:
        raise NoPermissionError(NoPermissionError.message)
    if task.status == u'审批中' or task.change_result == u'修改内容审批中':
        raise ConflictError(ConflictError.message)
    else:
        level = get_level()
        if int(task_info.risk_level) >= int(level):
            task_info.update(task_id=task.id, status=u'审批中',)
            _create(TaskReview, task_info)
            task.update(change_result=u'修改内容审批中')
            return task
        task.update(**task_info)
        return task

def _start_or_stop_task(args, task_id, update_task_list):
    task = get_task_with_id(task_id)
    jobs = task.jobs.all()
    if jobs:
        raise ConflictError(ConflictError.message)
    else:
        task.update(updated_at=datetime.now(), is_enable=args.is_enable)
        update_task_list.append(task)
        return task

def start_or_stop_tasks(args):
    """
    Start or stop task with task id
    Args:
        args: ID for task item

    Returns:
        Just the task items with this task_ids.
    """
    update_task_list = []
    for task_id in args.task_ids:
        _start_or_stop_task(args, task_id, update_task_list)
    return update_task_list



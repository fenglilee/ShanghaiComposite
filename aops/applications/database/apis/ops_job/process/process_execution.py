#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 2018/7/28 13:19
# @Author  : szf
import json
import datetime
from flask import request, session
from sqlalchemy.orm.exc import NoResultFound

from aops.applications.common.scheduler_request import SchedulerApi
from aops.applications.database.apis.resource.host.host import get_host_ips_with_ids

from aops.applications.database.models import ProcessExecution
from aops.applications.database.apis.ops_job.process import process as process_api
from aops.applications.exceptions.exception import ResourcesNotFoundError, ResourceAlreadyExistError

LOGIN_NAME = 'zhangsan'


def get_process_execution_list(execution_type, page, per_page, process_name=None):
    """
    Get all timed process items with query filter
    Returns:
        timed process list
    """

    processes = ProcessExecution.query.filter_by(is_deleted=False, execution_type=execution_type). \
        order_by(ProcessExecution.updated_at.desc())

    # Precise query
    if process_name:
        processes = processes.filter(ProcessExecution.name.like("%{}%".format(process_name)))

    try:
        # get process item by paginate
        processes = processes.paginate(page=page, per_page=per_page)
    except Exception as e:
        raise ResourcesNotFoundError("TIMED PROCESS")
    return processes


def get_process_execution_with_id(identifier):
    """
    Get a timed process with identifier
    Args:
        identifier: ID for timed process item

    Returns:
        Just the timed process item with this ID

    Raises:
        ResourcesNotFoundError: timed process is not found
    """
    try:
        process = ProcessExecution.query.filter_by(id=identifier, is_deleted=False).one()
    except ResourcesNotFoundError as e:
        raise ResourcesNotFoundError('ProcessExecution', e.message)
    return process


def create_process_execution(args):
    """
    Create a process instance with args from process template
    Args:
        args:dict which contain (process_id)

    Returns:
        the created timed process
    """
    login_name = session.get('user_info').get('user')

    process = process_api.get_process_with_id(args.process_id)

    instance_name = process.name if 'instant' == args.execution_type else args.name

    process_execution = ProcessExecution.query.filter_by(name=instance_name).first()
    if process_execution and not process_execution.is_deleted:
        raise ResourceAlreadyExistError('ProcessExecution')

    if process_execution and process_execution.is_deleted:
        process_execution.name = process.name + '_is_deleted_' + str(process_execution.id)

    if 'instant' == args.execution_type:
        data = {
            'execution_type': args.execution_type,
            'name': process.name,
            'creator': login_name,
            'description': process.description,
            'status': 0,    # disabled
            'risk_level': process.risk_level,
            'execution_account': process.execution_account,
            'success_rate': process.success_rate,
            'has_manual_job':process.has_manual_job,
            'scheduling': process.scheduling,
            'business_group': process.business_group,
            'process_id': args.process_id
        }

    if 'timed' == args.execution_type:
        data = {
            'execution_type': args.execution_type,
            'name': args.name,
            'creator': login_name,
            'description': args.description,
            'status': 0,
            'risk_level': process.risk_level,
            'execution_account': process.execution_account,
            'success_rate': process.success_rate,
            'has_manual_job': process.has_manual_job,
            'scheduling': process.scheduling,
            'business_group': process.business_group,
            'timed_type' : args.timed_type,
            'timed_config': args.timed_config,
            'timed_date': args.timed_date,
            'timed_expression': args.timed_expression,
            'process_id': args.process_id
        }

    return ProcessExecution.create(**data)


def delete_process_execution_with_id(identifier):
    """
    Delete a timed process with its id
    Args:
        identifier: the ID for timed process item
    Return:
        The deleted timed-process item
    """
    try:
        process_execution = ProcessExecution.query.filter_by(id=identifier, is_deleted=False).one()
    except NoResultFound as e:
        raise ResourcesNotFoundError('ProcessExecution')
    return process_execution.update(is_deleted=True, deleted_at=datetime.datetime.now())


def delete_process_execution_with_ids(identifiers):
    """
    Delete multiple processes with ids
    Args:
        identifiers: ID list for process items

    Returns:
        Just the deleted processes items
    """
    deleted_process_list = []

    for identifier in identifiers:
        result = delete_process_execution_with_id(identifier)
        deleted_process_list.append(result)

    return deleted_process_list


def update_status_with_ids(process_ids, status):
    """
    Update status for multiple process with ids
    Args:
        process_ids : the ID list of processes
        status: the updated status value
    Return:
        updated processes items
    """
    updated_executions = []
    executions = ProcessExecution.query.filter(ProcessExecution.id.in_(process_ids)).all()

    for execution in executions:
        updated_executions.append(execution.update(updated_at=datetime.datetime.now(), status=status))

    return updated_executions


def update_status_with_id(process_id, status):
    """
    Update status for one process with id
    Args:
        process_id : the ID list of processes
        status: the updated status value
    Return:
        updated process item
    """
    process = ProcessExecution.query.filter_by(id=process_id, is_deleted=False).one()
    return process.update(updated_at=datetime.datetime.now(), status=status)


def update_process_execution_with_id(identifier, updated_info):
    """
    Update single process execution with id
    Args:
        identifier: the id of some process
        updated_info: updated information for process
    Return:
        the updated process execution
    """
    try:
        process = ProcessExecution.query.filter_by(id=identifier, is_deleted=False).one()
    except ResourcesNotFoundError as e:
        raise ResourcesNotFoundError('Process', e.message)

    data = {
        'scheduling': updated_info.scheduling,
    }

    if hasattr(updated_info, 'timed_type'):    # timed config for timed prosess
        data.update({
            'description': updated_info.description,
            'timed_type': updated_info.timed_type,
            'timed_config': updated_info.timed_config,
            'timed_date': updated_info.timed_date,
            'timed_expression': updated_info.timed_expression
        })

    return process.update(**data)


def get_filter_list(execution_type):
    """
    Get all filters list

    Return:
         filters list including process_names
    """
    process_names = set()

    all_processes = ProcessExecution.query.filter_by(is_deleted=False, execution_type=execution_type).all()
    for process in all_processes:
        process_names.add(process.name)
    return process_names

def _get_target_ip(process_info):
    scheduling = []
    for job in json.loads(process_info['scheduling']):
        if 'target_ip' in job.keys():
            target_ip = get_host_ips_with_ids(job['target_ip'].split(','))
            job.update(target_ip=target_ip)
        scheduling.append(job)
    return scheduling

def execute_process(execution_type, process_info):
    """ execute a process by scheduler"""
    login_name = session.get('user_info').get('user')
    process_info = json.loads(process_info)
    scheduling = _get_target_ip(process_info)
    process_info.update(scheduling=json.dumps(scheduling), creator=login_name)

    if 'instant' == execution_type:
        process_info = json.dumps(process_info)
        data = {'flow_info': process_info}
        return SchedulerApi("/v1/instant-flows/").post(json=data)

    if 'timed' == execution_type:
        if process_info['status']:
            raise ResourceAlreadyExistError("{}".format('TimeProcess'))

        if process_info['timed_type'] == u'cycle':
            process_info = json.dumps(process_info)
            data = {'flow_info': process_info}
            # process_id = process_info['id']
            # execution_id = SchedulerApi('/v1/once-flows/').post(json=data)
            #
            # update_data = {
            #     'status': 1,
            #     'execution_id': execution_id,
            # }
            # timed_process = get_process_execution_with_id(process_id)
            # timed_process.update(**update_data)
        else:
            process_info = json.dumps(process_info)
            data = {'flow_info': process_info}
            return SchedulerApi('/v1/once-flows/').post(json=data)


def continue_execute_process(execution_type, execution_id):
    """ execute a process by scheduler"""
    if 'instant' == execution_type:
        data = {'flow_id': execution_id}

        result = SchedulerApi("/v1/instant-flows/").post(json=data)
        return {'flow_id': result['flow_id']}

    if 'timed' == execution_type:
        return {'flow_id': 'faked timed process execution'}


def stop_process(execution_id):
    """ execute a process by scheduler"""

    result = SchedulerApi("/v1/flows/{}".format(execution_id)).delete()
    return {'execution_id': result['flow_id']}

#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 2018/7/28 13:19
# @Author  : szf

import datetime

from flask import session, request
from sqlalchemy.orm.exc import NoResultFound

from aops.applications.database.models import Process
from aops.applications.database.apis import job as job_api
from aops.applications.exceptions.exception import ResourcesNotFoundError, ResourceAlreadyExistError



def get_process_list(page, per_page, process_name=None, creator=None, start_time=None, end_time=None, job_id=None):
    """
    Get all process items with query filter
    Returns:
        process list
    """
    processes = Process.query.filter_by(is_deleted=False).order_by(Process.updated_at.desc())

    # Precise query
    if process_name:
        processes = processes.filter(Process.name.like("%{}%".format(process_name)))

    if creator:
        processes = processes.filter(Process.creator.like("%{}%".format(creator)))

    if start_time and end_time:
        processes = processes.filter(Process.created_at.between(start_time, end_time))

    try:
        # get process item by paginate
        processes = processes.paginate(page=page, per_page=per_page)
    except Exception as e:
        raise ResourcesNotFoundError("PROCESS")

    if job_id:
        try:
            target_job = job_api.get_job_with_id(job_id)
        except ResourcesNotFoundError as e:
            return []
        results = []
        for process in processes:
            for job in process.jobs:
                if target_job.name in job.name:
                    results.append(process)
        return results

    return processes


def get_process_with_id(identifier):
    """
    Get a process with identifier
    Args:
        identifier: ID for process item
    Returns:
        Just the process item with this ID

    Raises:
        ResourcesNotFoundError: process is not found
    """
    try:
        process = Process.query.filter_by(id=identifier, is_deleted=False).one()
    except NoResultFound as e:
        raise ResourcesNotFoundError('Process')
    return process


def create_process(args):
    """
    Create a process with args
    Args:
        args:dict which contain (process_name, process_location,process_ip, process_description)

    Returns:
        the created process
    """
    business_group = request.cookies.get('BussinessGroup')
    login_name = session.get('user_info').get('user')

    process = Process.query.filter_by(name=args.name).first()
    if process and not process.is_deleted:
        raise ResourceAlreadyExistError('Process')

    if process and process.is_deleted:
        process.name = args.name + '_is_deleted_' + str(process.id)

    jobs = [job_api.get_job_with_id(job_id) for job_id in args.job_id_list]
    data = {
        'name': args.name,
        'creator': login_name,
        'description': args.description,
        'risk_level': _get_process_risk_level(jobs),
        'status': args.status,
        'execution_account': 0,
        'success_rate': _get_porcess_success_rate(jobs),
        'has_manual_job':args.has_manual_job,
        'scheduling': args.scheduling,
        'business_group': business_group,
        'jobs': jobs
    }

    return Process.create(**data)


def _get_porcess_success_rate(jobs):
    """ the process success_rate is the average of success rate"""
    sum = 0
    for job in jobs:
        sum = sum + job.success_rate

    return sum/len(jobs)

def _get_process_risk_level(jobs):
    """ the maximum with in jobs' risk levels """
    risk_level = 1
    for job in jobs:
        if job.risk_level > risk_level:
            risk_level = job.risk_level

    return risk_level


def delete_process_with_id(process_id):
    """
    Delete a process with its id
    Args:
        process_id: the ID for process item
    Return:
        The delete process item
    """
    process = get_process_with_id(process_id)
    return process.update(is_deleted=True, deleted_at=datetime.datetime.now())


def delete_processes_with_ids(process_ids):
    """
    Delete multiple processes with ids
    Args:
        process_ids: ID list for process items

    Returns:
        Just the delete processes items
    """
    deleted_process_list = []

    for process_id in process_ids:
        result = delete_process_with_id(process_id)
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
    updated_processes = []
    processes = Process.query.filter(Process.id.in_(process_ids)).all()
    for process in processes:
        updated_processes.append(process.update(updated_at=datetime.datetime.now(), status=status))

    return updated_processes


def update_process_with_id(identifier, updated_info):
    """
    Update single process with id
    Args:
        identifier: the id of some process
        updated_info: updated information for process
    Return:
        the updated process
    """
    login_name = session.get('user_info').get('user')
    try:
        process = Process.query.filter_by(id=identifier, is_deleted=False).one()
    except ResourcesNotFoundError as e:
        raise ResourcesNotFoundError('Process', e.message)

    jobs = [job_api.get_job_with_id(job_id) for job_id in updated_info.job_id_list]

    data = {
        'name': updated_info.name,
        'creator': login_name,
        'description': updated_info.description,
        'risk_level': _get_process_risk_level(jobs),
        'status': updated_info.status,
        'execution_account': 0,
        'success_rate': _get_porcess_success_rate(jobs),
        'has_manual_job': updated_info.has_manual_job,
        'scheduling': updated_info.scheduling,
        'jobs': jobs
    }
    return process.update(**data)


def get_filter_list():
    """
    Get all filters list

    Return:
         filters list including creators, process_names, job_names
    """

    creators = set()
    process_names = set()
    job_names = set()
    all_processse = Process.query.filter_by(is_deleted=False).all()
    for process in all_processse:
        creators.add(process.creator)
        process_names.add(process.name)
        job_names = job_names.update([job.name for job in process.jobs])

    return {'creators': set(creators), 'process_names': process_names, 'job_names': job_names}


def copy_process(identifier, updated_info):

    login_name = session.get('user_info').get('user')
    process = get_process_with_id(identifier)

    copied_process = {
        'name': updated_info.name,
        'creator': login_name,
        'description': updated_info.description,
        'risk_level': process.risk_level,
        'status': updated_info.status,
        'execution_account': 0,
        'success_rate': process.success_rate,
        'has_manual_job':process.has_manual_job,
        'scheduling': process.scheduling,
        'jobs': process.jobs
    }
    return Process.create(**copied_process)


def get_creator_list():
    business_group = request.cookies.get('BussinessGroup')

    q = Process.query.filter_by(is_deleted=False, business_group=business_group)

    creator_list = {'creator': set([obj.creator for obj in q])}
    return creator_list


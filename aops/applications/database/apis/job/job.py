#!/usr/bin/env python
# -*- coding:utf-8 -*-
from datetime import datetime

from flask import request, session
from sqlalchemy.orm.exc import NoResultFound
from aops.applications.database.apis.job import get_creator_list

from aops.applications.database.apis.task.task import job_get_task
from aops.applications.database.models.job.job import Job, JobExecution
from aops.applications.exceptions.exception import ResourcesNotFoundError,\
    ResourceAlreadyExistError, NoTaskError, NoPermissionError, ResourcesNotDisabledError, ConflictError


def get_jobs_list(page, per_page, name=None, job_type=None, system_type=None, creator=None, start_time=None, end_time=None, fuzzy_query=None):
    """
    Get all job
    :return:
        Job list
    """
    business_group = request.cookies.get('BussinessGroup')

    q = Job.query.filter_by(is_deleted=False, business_group=business_group).order_by(Job.updated_at.desc())

    if name:
        q = q.filter(Job.name.like(u"%{}%".format(name)))

    if job_type:
        q = q.filter(Job.job_type.like(u"%{}%".format(job_type)))

    if creator:
        q = q.filter(Job.creator.like(u"%{}%".format(creator)))

    if system_type:
        q = q.filter(Job.system_type.like(u"%{}%".format(system_type)))

    if start_time and end_time:
        q = q.filter(Job.created_at.between(start_time, end_time))

    if fuzzy_query:
        q = q.filter(Job.name.concat(Job.name).concat(Job.type).concat(Job.job_system).concat(Job.creator).concat(Job.fuzzy_query).like(u"%{}%".format(fuzzy_query)))
    try:
        return q.paginate(page=page, per_page=per_page)
    except Exception as e:
        raise ResourcesNotFoundError("JOB")


def get_job_with_id(identifier):
    """
    Get a job with identifier
    Args:
        identifier: ID for job item

    Returns:
        Just the job item with this ID

    Raises:
          NotFoundError: job is not found
    """
    try:
        job = Job.query.filter_by(id=identifier, is_deleted=False).one()
    except NoResultFound:
        raise ResourcesNotFoundError('Job')
    return job

def get_job_with_enable(page, per_page, system_type=None, fuzzy_query=None):
    """
    Get a job with identifier
    Args:
        identifier: ID for job item

    Returns:
        Just the job item with this ID

    Raises:
          NotFoundError: job is not found
    """
    business_group = request.cookies.get('BussinessGroup')

    q = Job.query.filter_by(is_deleted=False, business_group=business_group, status=True)\
        .order_by(Job.updated_at.desc())

    if system_type:
        q = q.filter(Job.system_type.like(u"%{}%".format(system_type)))

    if fuzzy_query:
        q = q.filter(Job.name.concat(Job.name).concat(Job.job_type).concat(Job.creator).like(u"%{}%".format(fuzzy_query)))

    try:
        return q.paginate(page=page, per_page=per_page)
    except Exception as e:
        raise ResourcesNotFoundError("JOB")

def generate_job_risk_level(task_id_list):

    task_list = [job_get_task(task_id) for task_id in task_id_list]
    try:
        risk_level = max(map(int, [task.risk_level for task in task_list]))
    except Exception as e:
        raise NoTaskError(e.message)
    return {'risk_level': risk_level, 'task_list': task_list}

def create_job(args):
    """
    Create a job with args
    Args:
        args: dict which contain ()

    Returns:
        the created job
    """
    business_group = request.cookies.get('BussinessGroup')
    creator = session.get('user_info').get('user')

    result = generate_job_risk_level(args.task_id_list)
    data = {
        'name': args.name,
        'description': args.description,
        'creator': creator,
        'system_type': args.system_type,
        'target_ip': ','.join([str(s) for s in args.target_ip]),
        'risk_level': result['risk_level'],
        'status': args.status,
        'execution_account': args.execution_account,
        'scheduling': args.scheduling,
        'frequency': args.frequency,
        'success_rate': 0,
        'job_type': args.job_type,
        'task_id_list': ','.join([str(s) for s in args.task_id_list]),
        'business_group': business_group,
    }

    try:
        job = Job.create(**data)
    except ResourceAlreadyExistError:
        raise ResourceAlreadyExistError("{}".format('Job'))

    for task in result['task_list']:
        job.tasks.append(task)
    job.save()

    return job

def update_job_with_id(identifier, job_info):
    """
    Update a job with identifier
    Args:
        identifier: ID for job item
        job_info: update job with this info

    Returns:
        Just the job item with this ID.
    """
    login_name = session.get('user_info').get('user')

    result = generate_job_risk_level(job_info.task_id_list)

    job = get_job_with_id(identifier)
    if job.creator != login_name:
        raise NoPermissionError(NoPermissionError.message)
    if job.status == True:
        raise ResourcesNotDisabledError('Job', identifier)
    job_info.update(updated_at=datetime.now(), task_id_list=','.join([str(s) for s in job_info.task_id_list]),
                    target_ip=','.join([str(s) for s in job_info.target_ip]), risk_level=result['risk_level'])
    job.update(**job_info)
    [job.tasks.remove(task) for task in job.tasks.all()]
    for task in result['task_list']:
        job.tasks.append(task)
    job.save()
    return job

def _start_or_stop_job(job_id, update_job_list, args):
    job = get_job_with_id(job_id)
    used_job_list = JobExecution.query.filter_by(is_deleted=False, job_id=job_id).all()
    if used_job_list:
        raise ConflictError(ConflictError.message)
    job.update(updated_at=datetime.now(), status=args.status)
    update_job_list.append(job)
    return job

def start_or_stop_jobs(args):
    """
    Start or stop job with job id
    Args:
        args: ID for job item

    Returns:
        Just the job items with this job_ids.
    """
    update_job_list = []

    for job_id in args.job_ids:
        _start_or_stop_job(job_id, update_job_list, args)
    return update_job_list

def _delete_job_with_id(job_id, deleted_job_list):
    job = get_job_with_id(job_id)
    if job.status == False:
        Job.soft_delete_by(id=job_id)
        job.name = job.name + '-' + str(datetime.now())
        deleted_job_list.append(job)
        return job
    raise ResourcesNotDisabledError('Job', job_id)

def delete_jobs_with_ids(args):
    """
    Delete job with job_ids
    Args:
        job_ids: ID for job item

    Returns:
        Just the job items with this job_ids.
    """
    deleted_job_list = []
    for job_id in args.job_ids:
        _delete_job_with_id(job_id, deleted_job_list)
    return deleted_job_list

def get_job_creator():

    business_group = request.cookies.get('BussinessGroup')

    return get_creator_list(object=Job, business_group=business_group)



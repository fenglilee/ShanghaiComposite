#!/usr/bin/env python
# -*- coding:utf-8 -*-
import json

from flask import request, session
from sqlalchemy.orm.exc import NoResultFound

from aops.applications.common.scheduler_request import SchedulerApi
from aops.applications.database.apis.job import get_creator_list
from aops.applications.database.apis.job.job import get_job_with_id
from aops.applications.database.apis.resource.host.host import get_host_ips_with_ids
from aops.applications.database.models.job.job import JobExecution
from aops.applications.exceptions.exception import ResourcesNotFoundError, ResourceNotFoundError, \
    ResourceAlreadyExistError, ResourcesNotDisabledError


def get_timed_jobs_list(page, per_page, name=None, system_type=None, job_type=None, target_ip=None, creator=None, start_time=None, end_time=None, fuzzy_query=None):
    """
    Get all timed job
    :return:
        timed Job list
    """
    business_group = request.cookies.get('BussinessGroup')

    q = JobExecution.query.filter_by(is_deleted=False, business_group=business_group, execution_type='timed')\
        .order_by(JobExecution.updated_at.desc())

    if name:
        q = q.filter(JobExecution.name.like(u"%{}%".format(name)))

    if system_type:
        q = q.filter(JobExecution.system_type.like(u"%{}%".format(system_type)))

    if job_type:
        q = q.filter(JobExecution.job_type.like(u"%{}%".format(job_type)))

    if target_ip:
        q = q.filter(JobExecution.target_ip.like(u"%{}%".format(target_ip)))

    if creator:
        q = q.filter(JobExecution.creator.like(u"%{}%".format(creator)))

    if start_time and end_time:
        q = q.filter(JobExecution.created_at.between(start_time, end_time))

    try:
        return q.paginate(page=page, per_page=per_page)
    except Exception as e:
        raise ResourcesNotFoundError("JobExecution")

def get_timed_job_with_id(identifier):
    """
    Get a timed job with identifier
    Args:
        identifier: ID for timed job item

    Returns:
        Just the timed job item with this ID

    Raises:
          NotFoundError: timed job is not found
    """
    try:
        timed_job = JobExecution.query.filter_by(id=identifier, is_deleted=False).one()
    except NoResultFound:
        raise ResourceNotFoundError('JobExecution', identifier)
    return timed_job

def create_timed_job(args):
    """
    Create a timed job with args
    Args:
        args: dict which contain ()

    Returns:
        the created timed job
    """
    creator = session.get('user_info').get('user')
    job = get_job_with_id(args.job_id)
    data = {
        'system_type': job.system_type,
        'risk_level': job.risk_level,
        'scheduling': job.scheduling,
        'success_rate': job.success_rate,
        'applications': job.applications,
        'job_type': job.job_type,
        'job_id': job.id,
        'execution_type': 'timed',
        'business_group': job.business_group,

        'name': args.name,
        'execution_account': args.execution_account,
        'target_ip': ','.join([str(s) for s in args.target_ip]),
        'frequency': args.frequency,
        'description': args.description,
        'timed_type': args.timed_type,
        'timed_expression': args.timed_expression,
        'timed_config': args.timed_config,
        'timed_date': args.timed_date,
        'executions_num': 0,
        'status': 0,
        'creator': creator,
    }
    try:
        job = JobExecution.create(**data)
    except ResourceAlreadyExistError:
        raise ResourceAlreadyExistError("{}".format('Job'))
    return job


def update_timed_job_with_id(identifier, execution_account=None, target_ip=None, frequency=None, scheduling=None,
                             description=None, timed_config=None, timed_expression=None, timed_date=None, timed_type=None):
    """
    Update a timed job with identifier
    Args:
        identifier: ID for timed job item
        job_info: update timed job with this info

    Returns:
        Just the timed job item with this ID.
    """
    login_name = session.get('user_info').get('user')

    data = {
        'creator': login_name,
        'execution_account': execution_account,
        'target_ip': ','.join(target_ip),
        'frequency': frequency,
        'scheduling': scheduling,
        'description': description,
        'timed_config': timed_config,
        'timed_expression': timed_expression,
        'timed_date': timed_date,
        'timed_type': timed_type,
    }
    timed_job = get_timed_job_with_id(identifier)
    timed_job.update(**data)
    return timed_job

def _delete_job_with_id(job_id, deleted_job_list):
    job = get_timed_job_with_id(job_id)
    if job.status == False:
        JobExecution.soft_delete_by(id=job_id)
        deleted_job_list.append(job)
        return job
    raise ResourcesNotDisabledError('Job', job_id)

def delete_timed_job_with_ids(args):
    """
    Delete instant job with job_ids
    Args:
        job_ids: ID for instant job item

    Returns:
        Just the instant job items with this job_ids.
    """
    deleted_job_list = []
    for job_id in args.job_ids:
        _delete_job_with_id(job_id, deleted_job_list)
    return deleted_job_list

def get_timed_creator():
    business_group = request.cookies.get('BussinessGroup')
    return get_creator_list(object=JobExecution, business_group=business_group, execution_type='timed')

def enable_timed_jobs(job_info):
    """
    enable a timed job with job id
    Args:
        args: ID for job item

    Returns:
        Just the timed job items with this job_ids.
    """
    login_name = session.get('user_info').get('user')
    job_info = json.loads(job_info)

    target_ip = get_host_ips_with_ids(job_info['target_ip'].split(','))

    job_info.update(creator=login_name, target_ip=target_ip)

    if job_info['status']:
        raise ResourceAlreadyExistError("{}".format('TimeJob'))

    if job_info['timed_type'] == u'cycle':
        job_id = job_info['id']
        job_info = json.dumps(job_info)
        data = {
            'job_info': job_info
        }
        execution_id = SchedulerApi('/v1/periodic-jobs/').post(json=data)
        update_data = {
            'status': 1,
            'execution_id': execution_id['job_id'],
        }
        timed_job = get_timed_job_with_id(job_id)
        timed_job.update(**update_data)

    else:
        job_info = json.dumps(job_info)
        data = {
            'job_info': job_info
        }
        return SchedulerApi('/v1/once-jobs/').post(json=data)


def disable_periodic_jobs(execution_id, id):
    """
    disable a timed job with job id
    Args:
        args: ID for job item

    Returns:
        Just the timed job items with this job_ids.
    """
    timed_job = get_timed_job_with_id(id)
    if not timed_job.status:
        # 判断是否已经停用
        raise ResourceAlreadyExistError("{}".format('TimeJob'))

    result = SchedulerApi('/v1/periodic-jobs/{}'.format(execution_id)).delete()
    if result == 200:
        update_data = {
            'status': 0,
            'execution_id': '',
        }
        timed_job.update(**update_data)
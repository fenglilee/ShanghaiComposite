#!/usr/bin/env python
# -*- coding:utf-8 -*-
from datetime import datetime
import json

from flask import request, session
from sqlalchemy.orm.exc import NoResultFound

from aops.applications.common.scheduler_request import SchedulerApi
from aops.applications.database.apis.approval.approval import create_approval
from aops.applications.database.apis.job import get_creator_list, DateEncoder, workday
from aops.applications.database.apis.job.job import get_job_with_id
from aops.applications.database.apis.resource.host.host import get_host_ips_with_ids
from aops.applications.database.models.job.job import JobExecution
from aops.applications.exceptions.exception import ResourcesNotFoundError, ResourceAlreadyExistError, \
    ResourceNotFoundError


def get_instant_jobs_list(page, per_page):
    """
    Get all instant job
    :return:
        instant Job list
    """
    business_group = request.cookies.get('BussinessGroup')
    login_name = session.get('user_info').get('user')

    q = JobExecution.query.filter_by(is_deleted=False, creator=login_name, business_group=business_group,
                                     execution_type='instant').order_by(JobExecution.updated_at.desc())
    try:
        return q.paginate(page=page, per_page=per_page)
    except Exception as e:
        raise ResourcesNotFoundError("JobExecution")

def get_instant_job_with_id(identifier):
    """
    Get a instant job with identifier
    Args:
        identifier: ID for instant job item

    Returns:
        Just the instant job item with this ID

    Raises:
          NotFoundError: instant job is not found
    """
    try:
        instant_job = JobExecution.query.filter_by(id=identifier, is_deleted=False).one()
    except NoResultFound:
        raise ResourceNotFoundError('JobExecution', identifier)
    return instant_job

def create_instant_job(args):
    """
    Create a instant job with args
    Args:
        args: dict which contain ()

    Returns:
        the created instant job
    """
    creator = session.get('user_info').get('user')
    job = get_job_with_id(args.job_id)
    data = {
        'name': job.name,
        'execution_account': job.execution_account,
        'target_ip': job.target_ip,
        'frequency': job.frequency,
        'description': job.description,
        'system_type': job.system_type,
        'risk_level': job.risk_level,
        'scheduling': job.scheduling,
        'success_rate': job.success_rate,
        'applications': job.applications,
        'job_type': job.job_type,
        'job_id': job.id,
        'execution_type': 'instant',
        'business_group': job.business_group,

        'result': 0,
        'creator': creator,
    }

    try:
        job = JobExecution.create(**data)
    except ResourceAlreadyExistError:
        raise ResourceAlreadyExistError("{}".format('Job'))
    return job

def update_instant_job_with_id(identifier, execution_account=None, target_ip=None, frequency=None, scheduling=None):
    """
    Update a instant job with identifier
    Args:
        identifier: ID for instant job item
        job_info: update instant job with this info

    Returns:
        Just the instant job item with this ID.
    """
    login_name = session.get('user_info').get('user')

    data = {
        'creator': login_name,
        'execution_account': execution_account,
        'target_ip': ','.join(target_ip),
        'frequency': frequency,
        'scheduling': scheduling,
    }
    instant_job = get_instant_job_with_id(identifier)
    instant_job.update(**data)
    return instant_job

def _delete_job_with_id(job_id, deleted_job_list):
    job = get_instant_job_with_id(job_id)
    JobExecution.soft_delete_by(id=job_id)
    deleted_job_list.append(job)
    return job

def delete_instant_job_with_ids(args):
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

def get_instant_creator():

    business_group = request.cookies.get('BussinessGroup')
    return get_creator_list(object=JobExecution, business_group=business_group, execution_type='instant')

def carry_out(job_info):
    """
    carry out a instant　job
    Args:
        job_info: this instant job info

    Returns: execution id

    """

    login_name = session.get('user_info').get('user')
    job_info = json.loads(job_info)
    target_ip = get_host_ips_with_ids(job_info['target_ip'].split(','))
    if workday():
        create_approval(operator=login_name, operation_type=1, task_name=job_info['name'], task_id=job_info['id'],
                        target=','.join(target_ip), risk=job_info['risk_level'], status='1', execute_time=datetime.now())
        return 200

    job_info.update(creator=login_name, target_ip=target_ip)
    job_info = json.dumps(job_info)
    data = {
        'job_info': job_info
    }
    return SchedulerApi('/v1/instant_jobs/').post(data=data)

def approval_execution(job_id):
    """
    Execution personnel pass after execution
    Args:
        job_id: job id

    Returns:

    """
    try:
        job_execution = JobExecution.query.filter_by(is_deleted=False, id=job_id).one()
    except Exception:
        raise ResourceNotFoundError('JobExecution', job_id)

    target_ip = get_host_ips_with_ids(job_execution.target_ip.split(','))

    job_execution_dict = job_execution.to_dict().update(target_ip=target_ip)
    job_info = json.dumps(job_execution_dict, cls=DateEncoder)
    data = {
        'job_info': job_info
    }
    return SchedulerApi('/v1/instant_jobs/').post(data=data)

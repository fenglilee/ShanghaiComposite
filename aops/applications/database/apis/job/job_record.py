#!/usr/bin/env python
# -*- coding:utf-8 -*-
from flask import request, session

from aops.applications.common.scheduler_request import SchedulerApi


def get_execution_record_list(page, per_page, execution_type, name=None, job_type=None, system_type=None, creator=None, target_ip=None, start_time=None, end_time=None, fuzzy_query=None):
    """
    Get all job record
    :return:
        Job record list
    """
    business_group = request.cookies.get('BussinessGroup', 'LDDS')

    data = {
        'page': page,
        'per_page': per_page,
        'execution_type': execution_type,
        'name': name,
        'job_type': job_type,
        'system_type': system_type,
        'creator': creator,
        'target_ip': target_ip,
        'start_time': start_time,
        'end_time': end_time,
        'business_group': business_group,
        'fuzzy_query': fuzzy_query,
    }
    return SchedulerApi('/v1/jobs/execution-record/').get(params=data)

def get_execution_record_creator(execution_type):

    business_group = request.cookies.get('BussinessGroup')
    data = {
        'business_group': business_group,
        'execution_type': execution_type,
    }
    return SchedulerApi('/v1/jobs/execution-record/creator/').get(params=data)

def execution_again(args):
    """
    carry out a job again
    Args:
        args: This job's job info and execution id

    Returns:execution id

    """
    login_name = session.get('user_info').get('user')
    data = {
        'execution_id': args,
        'creator': login_name
    }
    return SchedulerApi('/v1/jobs/execution-record/execution').post(data=data)


def stop_job_by_execution_id(args):
    """
    carry out a job again
    Args:
        args: This job's job info and execution id

    Returns:execution id

    """
    data = {
        'job_id': args,
    }
    return SchedulerApi('/v1/revoke-jobs/').post(json=data)


def get_job_record_list(page, per_page, id=None, execution_type=None, creator=None, execution_id=None, name=None, job_type=None, system_type=None, target_ip=None, start_time=None, end_time=None, fuzzy_query=None):
    """
    Get all job record
    :return:
        Job record list
    """
    business_group = request.cookies.get('BussinessGroup')

    data = {
        'page': page,
        'per_page': per_page,
        'id': id,
        'execution_type': execution_type,
        'creator': creator,
        'execution_id': execution_id,
        'name': name,
        'job_type': job_type,
        'system_type': system_type,
        'target_ip': target_ip,
        'business_group': business_group,
        'start_time': start_time,
        'end_time': end_time,
        'fuzzy_query': fuzzy_query,
    }
    return SchedulerApi('/v1/jobs/job-record/').get(params=data)

def get_job_record_creator():

    business_group = request.cookies.get('BussinessGroup')

    data = {
        'business_group': business_group,
    }
    return SchedulerApi('/v1/jobs/job-record/creator/').get(params=data)

def get_job_execution_log(args):
    """
    get execution log with job
    Returns:
        execution log
    """
    data = {
        'execution_id': args.execution_id,
        'target_ip': args.target_ip,
    }
    return SchedulerApi('/v1/jobs/job-record/log/').get(params=data)

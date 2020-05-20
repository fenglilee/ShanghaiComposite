#!/usr/bin/env python
# -*- coding:utf-8 -*-
from flask import request

from aops.applications.common.scheduler_request import SchedulerApi

def get_daily_job_result_list(page, per_page, name=None, system_type=None, creator=None):
    """
    Get all job record
    :return:
        Job record list
    """
    business_group = request.cookies.get('BussinessGroup')

    data = {
        'page': page,
        'per_page': per_page,
        'name': name,
        'system_type': system_type,
        'creator': creator,
        'business_group': business_group,
    }
    return SchedulerApi('/v1/daily/execution-record/').get(params=data)

def get_daily_host_result_list(page, per_page, name=None, system_type=None, execution_id=None, target_ip=None, result=None, item=None, start_time=None, end_time=None):
    """
    Get all DailyInspection
    :return:
        DailyInspection list
    """
    business_group = request.cookies.get('BussinessGroup')

    data = {
        'page': page,
        'per_page': per_page,
        'system_type': system_type,
        'name': name,
        'item': item,
        'result': result,
        'target_ip': target_ip,
        'start_time': start_time,
        'end_time': end_time,
        'execution_id': execution_id,
        'business_group': business_group,
    }
    return SchedulerApi('/v1/daily/job-record/').get(params=data)
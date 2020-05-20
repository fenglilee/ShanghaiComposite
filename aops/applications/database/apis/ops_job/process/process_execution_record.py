#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 2018/7/28 13:19
# @Author  : szf


from aops.applications.common.scheduler_request import SchedulerApi

LOGIN_NAME = 'zhangsan'
ENDPOINT = '/v1/flow-records'

def get_execution_record_list(execution_type, page, per_page, start_time=None, end_time=None):
    """
    Get all process items with query filter from Scheduler
    Returns:
        execution records list
    """
    params = {
        'execution_type': execution_type,
        'page': page,
        'per_page': per_page,
        'start_time': start_time,
        'end_time': end_time
    }
    return SchedulerApi(ENDPOINT).get(params=params)


def get_execution_record_id(identifier):
    """
    Get a process with identifier from Scheduler
    Args:
        identifier: ID for execution record item

    Returns:
        Just the execution record item with this ID

    Raises:
        ResourcesNotFoundError: execution record is not found
    """
    return SchedulerApi(ENDPOINT + '/' + identifier).get()








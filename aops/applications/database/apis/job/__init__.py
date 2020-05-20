#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 18-7-3 上午9:30
# @Author  : Hbs
import time
import json
from datetime import date, datetime
from flask import current_app
from aops.applications.database.apis.system.sysconfig.exchange_config import get_exchange_configs


def get_creator_list(object, business_group, execution_type=None):
    """
    Get all task creator
    Returns:
        all task creator
    """

    if execution_type:
        q = object.query.filter_by(business_group=business_group, execution_type=execution_type).all()
    else:
        q = object.query.filter_by(business_group=business_group).all()

    creator_list = {'creator': set([obj.creator for obj in q])}
    return creator_list


class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.__str__()
        return json.JSONEncoder.default(self, obj)


def workday():
    """
    Determine whether the working day
    """
    exchange_configs = get_exchange_configs()
    if exchange_configs.get('is_on', 0):
        return 0
    worktime = [str(exchange_configs.get('start_time')), str(exchange_configs.get('end_time'))]
    dayofweek = datetime.now().weekday()
    # dayofweek = datetime.today().weekday()
    beginwork = datetime.now().strftime("%Y-%m-%d") + ' ' + worktime[0]
    endwork = datetime.now().strftime("%Y-%m-%d") + ' ' + worktime[1]
    beginworkseconds = time.time() - time.mktime(time.strptime(beginwork, '%Y-%m-%d %H:%M:%S'))
    endworkseconds = time.time() - time.mktime(time.strptime(endwork, '%Y-%m-%d %H:%M:%S'))
    if (int(dayofweek) in range(5)) and int(beginworkseconds) > 0 and int(endworkseconds) < 0:
        return 1
    else:
        return 0

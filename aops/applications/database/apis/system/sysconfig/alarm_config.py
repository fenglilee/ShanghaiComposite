#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 2018/7/19 15:35
# @Author  : szf


import json
from sqlalchemy.orm.exc import NoResultFound
from aops.applications.exceptions.exception import ResourceNotFoundError, ResourceAlreadyExistError

from aops.applications.database.models import SysConfigAlarm


def get_alarm_config():
    alarm_cfg = SysConfigAlarm.query.filter_by(is_deleted=False, key='alarm_config').first()
    if alarm_cfg:
        return json.loads(alarm_cfg.value)
    else:
        return None


def create_alarm_config(args):
    alarm_cfg = SysConfigAlarm.query.filter_by(is_deleted=False, key='alarm_config').first()
    data = {
        'value': json.dumps(args)
    }

    if alarm_cfg:
        alarm = alarm_cfg.update(**data)
    else:
        data.update({'key': 'alarm_config'})
        alarm = SysConfigAlarm.create(**data)

    return json.loads(alarm.value)



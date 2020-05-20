#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 2018/7/17 16:28
# @Author  : szf

from aops.applications.database import db
from ..system.user import User
from aops.applications.database.models.common import TimeUtilModel, MinModel


class SysConfigApprove(MinModel, TimeUtilModel):
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.Integer, unique=False, nullable=False)  # 1: low, 2: middle, 3: high
    script_on = db.Column(db.Integer, unique=False, nullable=False)
    software_on = db.Column(db.Integer, unique=False, nullable=False)
    config_on = db.Column(db.Integer, unique=False, nullable=False)


class SysConfigBusiness(MinModel, TimeUtilModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text, unique=False, nullable=False)


class SysConfigExchange(MinModel, TimeUtilModel):
    id = db.Column(db.Integer, primary_key=True)
    is_on = db.Column(db.Integer, unique=False, nullable=False)
    start_time = db.Column(db.Time(), unique=False, nullable=False)
    end_time = db.Column(db.Time(), unique=False, nullable=False)


# alarmUser = db.Table('alarm_user',
#     db.Column('alarm_id', db.Integer, db.ForeignKey('sys_config_alarm.id'), primary_key=True),
#     db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
# )

class SysConfigAlarm(MinModel, TimeUtilModel):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=False, nullable=False)   #'alarm_config'
    value = db.Column(db.Text, unique=False, nullable=False) # json_string



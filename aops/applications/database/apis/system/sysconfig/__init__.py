#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 2018/7/19 13:38
# @Author  : szf

from flask import current_app
from aops.applications.database.apis.system.sysconfig.alarm_config import create_alarm_config
from aops.applications.database.apis.system.sysconfig.approve_config import create_approve_config
from aops.applications.database.apis.system.sysconfig.exchange_config import create_exchange_config


def init_system_config():
    default_approve = {
        'level': 1,
        "config_on": 0,
        "software_on": 0,
        "script_on": 0
    }
    default_alarm = {
        "daily_check": {  # 日常检查
            "alarm_on": 0,       # 是否开启告警 0：关闭，1：开启
            "risk_alarm_to": [],  # 风险事件告警人 ids
            "risk_alarm_by": [],  # 风险事件告警方式， 微信，邮件，短信
            "except_alarm_to": [],  # 异常事件告警人
            "except_alarm_by": []   # 异常事件告警方式
        },
        "timed_job": {  # 定时作业
            "alarm_to": [],
            "alarm_on": 0,
            "alarm_by": []
        }
    }
    default_exchange = {
        "is_on": 0,
        "start_time": '08:00:00',
        "end_time": '09:00:00'
    }
    current_app.logger.info("Init System Config with args: approve_conifg: {}, alarm config: {}, exchange config: {}".
                            format(default_approve, default_alarm, default_exchange))
    approve_cfg = create_approve_config(default_approve)
    alarm_cfg = create_alarm_config(default_alarm)
    exchange_cfg = create_exchange_config(default_exchange)

    current_app.logger.info("Init System Config's results: approve config: {}, alarm config: {}, exchange config: {}".
                            format(approve_cfg.to_dict(), alarm_cfg, exchange_cfg.to_dict()))

    return approve_cfg, alarm_cfg, exchange_cfg

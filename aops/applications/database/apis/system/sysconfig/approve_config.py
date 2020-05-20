#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 2018/7/19 15:34
# @Author  : szf

import datetime
from sqlalchemy.orm.exc import NoResultFound
from aops.applications.exceptions.exception import ResourceNotFoundError, ResourceAlreadyExistError

from aops.applications.database.models import SysConfigApprove


# Approve config APIs
def get_approve_configs():
    try:
        approve_config = SysConfigApprove.query.filter_by(is_deleted=False).one()
    except NoResultFound:
        # raise ResourceNotFoundError('ApproveConfig')
        return {}
    return approve_config

# only one item in db
def create_approve_config(args):
    data = {
        'level': args['level'],
        "config_on": args['config_on'],
        "software_on": args['software_on'],
        "script_on": args['script_on']
    }
    approve_cfg = SysConfigApprove.query.filter_by(is_deleted=False).first()
    if approve_cfg:    # Already exist, update
        return approve_cfg.update(**data)
    else:
        return SysConfigApprove.create(**data)
#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 2018/7/19 15:34
# @Author  : szf

import datetime
from sqlalchemy.orm.exc import NoResultFound
from aops.applications.exceptions.exception import ResourceNotFoundError, ResourcesNotFoundError, ResourceAlreadyExistError

from aops.applications.database.models import SysConfigExchange


# exchange config APIs
def get_exchange_configs():
    try:
        exchange_config = SysConfigExchange.query.filter_by(is_deleted=False).one()
    except NoResultFound:
        # raise ResourcesNotFoundError('exchangeConfig')
        return {}
    return exchange_config.to_dict()


# only one item in db
def create_exchange_config(args):
    data = {
        "is_on": args['is_on'],
        "start_time": args['start_time'],
        "end_time": args['end_time']
    }
    exchange_cfg = SysConfigExchange.query.filter_by(is_deleted=False).first()
    if exchange_cfg:
        return exchange_cfg.update(**data)
    else:
        return SysConfigExchange.create(**data)



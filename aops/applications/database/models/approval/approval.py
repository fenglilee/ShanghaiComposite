# !/usr/bin/python
# -*- coding:utf-8 -*-

"""
@author: fengli
@time: 2018/8/11 下午1:45
@file: approval
"""

import enum
from aops.applications.database import db
from aops.applications.database.models.common import TimeUtilModel
from aops.applications.database.models.common import MinModel


class OperationType(enum.Enum):

    scheduler_ops = 1
    realtime_ops = 2
    scheduler_flow = 3
    realtime_flow = 4


class OperationStatus(enum.Enum):

    processing = 1
    passed = 2
    rejected = 3


class Approval(TimeUtilModel, MinModel):

    __tablename__ = 'approval'

    id = db.Column(db.Integer, primary_key=True)
    # submit_time = db.Column(db.DateTime, nullable=False, default=datetime.now())
    task_id = db.Column(db.Integer, nullable=False)
    task_name = db.Column(db.String(64), nullable=False)
    tmp_id = db.Column(db.Integer, nullable=False)
    operator = db.Column(db.String(64), nullable=False)
    operation_type = db.Column(db.String(64), nullable=False)
    target = db.Column(db.String(64), nullable=False)
    execute_time = db.Column(db.DateTime, nullable=False)
    risk = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(64), nullable=False)
    approver = db.Column(db.String(64), nullable=True)
    description = db.Column(db.String(128), nullable=True)


if __name__ == '__main__':
    pass


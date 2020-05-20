# !/usr/bin/python
# -*- coding:utf-8 -*-

"""
@author: fengli
@time: 2018/8/13 上午9:32
@file: approval
"""

from datetime import datetime
from sqlalchemy import desc
from flask import current_app as app
from aops.applications.exceptions.exception import ResourceNotFoundError
from aops.applications.exceptions.exception import ValidationError
from aops.applications.database.models.approval.approval import Approval


def get_approvals(**kwargs):
    page = kwargs['page']
    per_page = kwargs['per_page']
    start_time = kwargs['start_time']
    end_time = kwargs['end_time']
    operator = kwargs['operator']
    operation_type = kwargs['operation_type']
    task_name = kwargs['task_name']
    approver = kwargs['approver']
    status = kwargs['status']
    approvals = Approval.query.filter_by(is_deleted=False).order_by(desc(Approval.updated_at))

    date_format = app.config.get("DATE_FORMAT")
    if start_time is not None:
        start_time = datetime.strptime(start_time, date_format)
        approvals = approvals.filter(Approval.created_at >= start_time)
    if end_time is not None:
        end_time = datetime.strptime(end_time, date_format)
        approvals = approvals.filter(Approval.created_at <= end_time)
    if operator is not None:
        approvals = approvals.filter(Approval.operator == operator)
    if operation_type is not None:
        approvals = approvals.filter(Approval.operation_type == operation_type)
    if task_name is not None:
        approvals = approvals.filter(Approval.task_name == task_name)
    if approver is not None:
        approvals = approvals.filter(Approval.approver == approver)
    if status is not None:
        approvals = approvals.filter(Approval.status == status)
    try:
        return approvals.paginate(page=page, per_page=per_page)
    except Exception as e:
        raise ResourceNotFoundError('Approval', e.message)


def create_approval(**kwargs):
    date_format = app.config.get("DATE_FORMAT")
    if not isinstance(kwargs['execute_time'], datetime):
        kwargs['execute_time'] = datetime.strptime(kwargs['execute_time'], date_format)
    old_record = Approval.query.filter_by(task_id=kwargs['task_id']).first()
    if old_record is not None:
        raise ValidationError(u'approval for present task has already been created')
    new_record = Approval.create(**kwargs)
    return new_record


def update_approval_with_id(identifier, **kwargs):
    approval = Approval.query.filter_by(id=identifier, status='1', is_deleted=False).first()
    if approval is None:
        raise ResourceNotFoundError('Approval', identifier)
    return approval.update(updated_at=datetime.now(), **kwargs)


if __name__ == '__main__':
    pass


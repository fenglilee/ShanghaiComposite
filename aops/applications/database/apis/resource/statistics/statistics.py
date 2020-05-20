# !/usr/bin/python
# -*- coding:utf-8 -*-

"""
@author: fengli
@time: 2018/8/21 下午4:19
@file: statistics
"""

from flask import current_app as app
from datetime import datetime, timedelta
from aops.applications.database.models.resource.host import Host
from aops.applications.database.models.resource.application import Application
from aops.applications.database.models.repository.risk_command import RiskRepository, CommandWhiteList
from aops.applications.database.models.repository.repository import RepositoryModel
from aops.applications.exceptions.exception import ResourcesNotFoundError, Error


def count_hosts(start_time=None, end_time=None, business=None):
    if business:
        q = Host.query.filter_by(is_deleted=False, business=business)
    else:
        q = Host.query.filter_by(is_deleted=False)
    date_format = app.config.get("DATE_FORMAT")
    if start_time is not None:
        start_time = datetime.strptime(start_time, date_format)
        q = q.filter(Host.updated_at >= start_time)
    if end_time is not None:
        end_time = datetime.strptime(end_time, date_format)
        q = q.filter(Host.updated_at >= end_time)

    try:
        count = q.count()
        return dict(count=count)
    except Exception as e:
        raise ResourcesNotFoundError('{}'.format(e))


def count_applications(start_time=None, end_time=None, business_group=None):
    if business_group:
        q = Application.query.filter_by(is_deleted=False, business_group=business_group)
    else:
        q = Application.query.filter_by(is_deleted=False)
    date_format = app.config.get("DATE_FORMAT")
    if start_time is not None:
        start_time = datetime.strptime(start_time, date_format)
        q = q.filter(Application.updated_at >= start_time)

    if end_time is not None:
        end_time = datetime.strptime(end_time, date_format)
        q = q.filter(Application.updated_at <= end_time)

    try:
        count = q.count()
        return dict(count=count)
    except Exception as e:
        raise ResourcesNotFoundError('{}'.format(e))


def count_risk_commands(start_time=None, end_time=None, business_group=None):
    if business_group:
        rq = RiskRepository.query.filter_by(is_deleted=False, business_group=business_group)
        cq = CommandWhiteList.query.filter_by(is_deleted=False, business_group=business_group)
    else:
        rq = RiskRepository.query.filter_by(is_deleted=False)
        cq = CommandWhiteList.query.filter_by(is_deleted=False)

    date_format = app.config.get("DATE_FORMAT")
    if start_time is not None:
        start_time = datetime.strptime(start_time, date_format)
        rq = rq.filter(RiskRepository.updated_at >= start_time)
        cq = cq.filter(CommandWhiteList.updated_at >= start_time)

    if end_time is not None:
        end_time = datetime.strptime(end_time, date_format)
        rq = rq.filter(RiskRepository.updated_at <= end_time)
        cq = cq.filter(CommandWhiteList.updated_at <= end_time)

    try:
        r_count = rq.count()
        c_count = cq.count()
        return dict(risks_count=r_count, commands_count=c_count)
    except Exception as e:
        raise ResourcesNotFoundError('{}'.format(e))


def number_file_commits(start_time=None, end_time=None, business_group=None):
    if business_group:
        ssq = RepositoryModel.query.filter_by(is_deleted=False, business_group=business_group). \
            filter(RepositoryModel.absolute_path.like(u"%{}%".format("/scripts/")))
        asq = RepositoryModel.query.filter_by(is_deleted=False, business_group=business_group). \
            filter(RepositoryModel.absolute_path.like(u"%{}%".format("/applications/")))
        csq = RepositoryModel.query.filter_by(is_deleted=False, business_group=business_group). \
            filter(RepositoryModel.absolute_path.like(u"%{}%".format("/configurations/")))
    else:
        ssq = RepositoryModel.query.filter_by(is_deleted=False, business_group=business_group).filter(
            RepositoryModel.absolute_path.like(u"%{}%".format("/scripts/")))
        asq = RepositoryModel.query.filter_by(is_deleted=False, business_group=business_group).filter(
            RepositoryModel.absolute_path.like(u"%{}%".format("/applications/")))
        csq = RepositoryModel.query.filter_by(is_deleted=False, business_group=business_group).filter(
            RepositoryModel.absolute_path.like(u"%{}%".format("/configurations/")))

    date_format = app.config.get("DATE_FORMAT")
    if start_time is None:
        start_time = datetime.date(datetime.now()) - timedelta(days=6)
    else:
        start_time = datetime.strptime(start_time, date_format)

    if end_time is None:
        end_time = datetime.date(datetime.now())
    else:
        end_time = datetime.strptime(end_time, date_format)

    if start_time > end_time:
        raise Error(u'开始时间大于结束时间，请重新选择时间', code=400)

    number_list = []
    between_end = end_time - start_time
    days = between_end.days

    time_list = [start_time]
    day = start_time
    for i in range(0, days):
        day = day + timedelta(1)
        time_list.append(day)
    try:
        for time in time_list:
            start = time
            end = start + timedelta(1)
            sitem_q = ssq.filter(RepositoryModel.updated_at >= start)
            sitem_q = sitem_q.filter(RepositoryModel.updated_at < end)
            scripts_count = sitem_q.count()

            aitem_q = asq.filter(RepositoryModel.updated_at >= start)
            aitem_q = aitem_q.filter(RepositoryModel.updated_at < end)
            applications_count = aitem_q.count()

            citem_q = csq.filter(RepositoryModel.updated_at >= start)
            citem_q = citem_q.filter(RepositoryModel.updated_at < end)
            configurations_count = citem_q.count()
            item = {
                'date': datetime.strftime(start, "%m/%d"),
                'scripts_count': scripts_count,
                'applications_count': applications_count,
                'configurations_count': configurations_count
            }
            number_list.append(item)
        return number_list
    except Exception as e:
        raise ResourcesNotFoundError('{}'.format(e))


if __name__ == '__main__':
    pass

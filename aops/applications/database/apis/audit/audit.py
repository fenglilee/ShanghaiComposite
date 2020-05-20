#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
from datetime import datetime
from flask import current_app as app
from aops.applications.database.models.audit.audit import Audit
from aops.applications.exceptions.exception import ResourcesNotFoundError


def get_audit_list():
    """
    Get audit list
    :return:
    """
    return Audit.query.filter_by(is_deleted=False).all()


def add_audit_item(**args):
    audit_item = Audit.create(**args)
    return audit_item.to_dict()


def get_audit_list(page, per_page, args):
    start_time = args.start_time
    end_time = args.end_time
    creator = args.user
    source_ip = args.source_ip
    resource_type = args.resource_type
    resource_id = args.resource_id
    operation = args.operation
    status = args.status
    message = args.message
    fq = args.fuzzy_query

    q = Audit.query.filter_by(is_deleted=False).order_by(Audit.updated_at.desc())

    if creator:
        q = q.filter(Audit.user.like("%{}%".format(creator)))

    date_format = app.config.get("DATE_FORMAT")
    if start_time:
        start_time = datetime.strptime(start_time, date_format)
        q = q.filter(Audit.created_at >= ("{}".format(start_time)))

    if end_time:
        end_time = datetime.strptime(end_time, date_format)
        q = q.filter(Audit.updated_at <= ("{}".format(end_time)))

    if source_ip:
        q = q.filter(Audit.source_ip.like("%{}%".format(source_ip)))

    if resource_type:
        q = q.filter(Audit.resource.like("%{}%".format(resource_type)))

    if resource_id:
        q = q.filter(Audit.resource_id.like("%{}%".format(resource_id)))

    if operation:
        q = q.filter(Audit.operation.like("%{}%".format(operation)))

    if status:
        q = q.filter(Audit.status.like("%{}%".format(result)))

    if message:
        q = q.filter(Audit.message.like("%{}%".format(message)))

    if fq:
        q = q.filter(Audit.name.concat(Audit.comment).like("%{}%".format(fq)))

    try:
        return q.paginate(page=page, per_page=per_page)
    except Exception as e:
        app.logger.error("Audit list failed: " + str(e))
        raise ResourcesNotFoundError("Audits")


def audit_list_search(args):
    source_ip = args.source_ip
    resource_type = args.resource_type
    resource_id = args.resource_id
    operation = args.operation
    status = args.status
    message = args.message

    q = Audit.query.filter_by(is_deleted=False).order_by(Audit.updated_at.desc())

    if source_ip:
        q = q.filter(Audit.source_ip.like("%{}%".format(source_ip)))

    if resource_type:
        q = q.filter(Audit.resource.like("%{}%".format(resource_type)))

    if resource_id:
        q = q.filter(Audit.resource_id.like("%{}%".format(resource_id)))

    if operation:
        q = q.filter(Audit.operation.like("%{}%".format(operation)))

    if status:
        q = q.filter(Audit.status.like("%{}%".format(result)))

    if message:
        q = q.filter(Audit.message.like("%{}%".format(message)))

    try:
        return q.all()
    except Exception as e:
        app.logger.error("Audit list failed: " + str(e))
        raise ResourcesNotFoundError("Audits")


def get_audit_user_list():
    q = Audit.query.filter_by(is_deleted=False).order_by(Audit.updated_at.desc())
    try:
        q_data = q.all()
    except Exception as e:
        app.logger.error("Audit list failed: " + str(e))
        raise ResourcesNotFoundError("Audits")
    return {'creator': set([obj.user for obj in q_data])}


def get_audit_resource_list():
    q = Audit.query.filter_by(is_deleted=False).order_by(Audit.updated_at.desc())
    try:
        q_data = q.all()
    except Exception as e:
        app.logger.error("Audit list failed: " + str(e))
        raise ResourcesNotFoundError("Audits")
    return {'resource': set([obj.resource for obj in q_data])}


def get_audits_csv(args):

    start_time = args.start_time
    end_time = args.end_time
    user = args.user
    source_ip = args.source_ip
    resource_type = args.resource_type
    resource_id = args.resource_id
    operation = args.operation
    result = args.result
    message = args.message

    q = Audit.query.filter_by(is_deleted=False).order_by(Audit.updated_at.desc())

    if user:
        q = q.filter(Audit.user.like("%{}%".format(user)))

    date_format = app.config.get("DATE_FORMAT")
    if start_time:
        start_time = datetime.strptime(start_time, date_format)
        q = q.filter(Audit.created_at >= ("{}".format(start_time)))

    if end_time:
        end_time = datetime.strptime(end_time, date_format)
        q = q.filter(Audit.updated_at <= ("{}".format(end_time)))

    if source_ip:
        q = q.filter(Audit.source_ip.like("%{}%".format(source_ip)))

    if resource_type:
        q = q.filter(Audit.resource.like("%{}%".format(resource_type)))

    if resource_id:
        q = q.filter(Audit.resource_id.like("%{}%".format(resource_id)))

    if operation:
        q = q.filter(Audit.operation.like("%{}%".format(operation)))

    if result:
        q = q.filter(Audit.operation_status.like("%{}%".format(result)))

    if message:
        q = q.filter(Audit.message.like("%{}%".format(message)))
    try:
        q_set = map(lambda item: item.to_dict(), q.all())
        print 'q_set length is here --->>>', len(q_set)
        keys = None
        audit_list = list()
        for audit in q_set:
            if keys is None:
                keys = audit.keys()
            value_list = list()
            for key in keys:
                value = str(audit[key])
                if ',' in value:
                    value = value.replace(',', '，')
                value_list.append(value.encode("GB18030", 'ignore'))
            audit_list.append(",".join(value_list))
        audit_list.insert(0, ",".join(keys))
        for audit in audit_list:
            yield audit + "\n"
        # audit_csv = "\n".join(audit_list)
        # return audit_csv
    except Exception as e:
        app.logger.error("Audit list failed: " + str(e))
        raise ResourcesNotFoundError("Audits")



#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 2018/7/26 19:27
# @Author  : szf

from sqlalchemy import desc, or_
from sqlalchemy.orm.exc import NoResultFound
from aops.applications.database.models import Message
from aops.applications.database.models import User
from aops.applications.database.apis.system.user import user as user_apis
from aops.applications.exceptions.exception import ResourceNotFoundError
from datetime import datetime
from flask import current_app as app
from flask import session


def get_message_list(page, per_page, start_time=None, end_time=None, type=None, risk_level=None, status=None):
    messages = Message.query.filter_by(is_deleted=False). \
        order_by(desc(Message.updated_at))

    username = session.get('user_info').get('user')
    user = user_apis.get_user_with_name(username=username)
    messages = messages.filter(Message.users.any(id=user.id))

    # Precise query
    if start_time and end_time:
        messages = messages.filter(Message.created_at.between(start_time, end_time))
    if type:
        messages = messages.filter(Message.classify.like("%{}%".format(type)))

    if risk_level:
        messages = messages.filter(Message.status.like("%{}%".format(risk_level)))
    if status:
        messages = messages.filter(Message.status.like("%{}%".format(status)))

    # return pagination body
    try:
        return messages.paginate(page=page, per_page=per_page)
    except Exception as e:
        raise ResourceNotFoundError('Message', e.message)


def get_unsent_messages():
    return Message.query.filter_by(is_deleted=False, is_sent=False).order_by(desc(Message.created_at)).all()


def create_message(**kwargs):
    message = Message(classify=kwargs['classify'],
                      risk_level=kwargs['risk_level'],
                      content=kwargs['content'],
                      status=kwargs['status'])
    users = user_apis.get_users_with_names(kwargs['usernames'])
    message.update(users=users)
    return message.save()


def count_user_message(identifier):
    user = User.query.filter_by(id=identifier, is_deleted=False).first()
    messages = user.messages
    unsent_messages = [message for message in messages if message.status == 2]
    return {'count': len(unsent_messages), 'username': user.username}


def update_message(identifier, classify=None, risk_level=None, content=None, status=None, created_at=None):
    try:
        message = Message.query.filter_by(id=identifier, is_deleted=False).one()
        update_body = dict()

        if classify is not None:
            update_body['classify'] = classify

        if risk_level is not None:
            update_body['risk_level'] = risk_level

        if content is not None:
            update_body['content'] = content

        if status is not None:
            update_body['status'] = status

        if created_at is not None:
            date_format = app.config.get("DATE_FORMAT")
            update_body['created_at'] = datetime.strptime(created_at, date_format)

        message = message.update(**update_body)
        return message
    except NoResultFound as e:
        ResourceNotFoundError('Message', '{}'.format(e))

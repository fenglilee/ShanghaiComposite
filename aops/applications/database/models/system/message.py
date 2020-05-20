#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 2018/7/26 14:48
# @Author  : szf

from aops.applications.database import db
from ..common import TimeUtilModel, MinModel
from .user import User

# many <-> many: message <-> user
MessageUser = db.Table('message_user',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('message_id', db.Integer, db.ForeignKey('message.id'), primary_key=True)
)


class Message(MinModel, TimeUtilModel):
    id = db.Column(db.Integer, primary_key=True)
    classify = db.Column(db.Integer, nullable=False)    # 0: notification, 1:confirmation
    risk_level = db.Column(db.Integer, nullable=False)  # 0:low, 1:middle, 2:high
    content = db.Column(db.String(200), nullable=False)
    status = db.Column(db.Integer, nullable=False)       # 0: confirmed, 1:non-confirmed, 2:unconfirmed,
    is_sent = db.Column(db.Integer, nullable=False, default=0)
    sent_by = db.Column(db.Integer, nullable=False, default=0)      # 0: message 1: wechat 2: email
    users = db.relationship(User, secondary=MessageUser, lazy='subquery',
                            backref=db.backref('messages', lazy=False))
#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 18-7-4 上午10:15
# @Author  : zsf

from aops.applications.database import db
from aops.applications.database.models.common import TimeUtilModel, MinModel

# one -> many: group -> Parameter, Host -> HAccount, Host -> HParameter
# many <-> many: group <-> host,

groupHost = db.Table('group_host',
    db.Column('host_id', db.Integer, db.ForeignKey('host.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True)
)


class Group(MinModel, TimeUtilModel):
    id = db.Column(db.Integer, primary_key=True)
    pid = db.Column(db.Integer, unique=False, nullable=False)
    name = db.Column(db.String(64), unique=True, nullable=False)
    business = db.Column(db.String(64), unique=False, nullable=False)  # LDDS, Cloud,...
    type = db.Column(db.String(64), unique=False, nullable=False)    # business, group
    is_read_only = db.Column(db.Integer, unique=False, nullable=False, default=0)   # 0: read only, 1: can be modified
    description = db.Column(db.Text, unique=False, nullable=True)
    modified_by = db.Column(db.String(64), unique=False, nullable=True)
    hosts = db.relationship('Host', secondary=groupHost, lazy=False,
                            backref=db.backref('groups', lazy=False))
    others = db.Column(db.String(64), unique=False, nullable=True)


class Host(MinModel, TimeUtilModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    type = db.Column(db.String(64), unique=False, default='host', nullable=False)   # host
    business = db.Column(db.String(64), unique=False, nullable=False) # LDDS
    identity_ip = db.Column(db.String(64), unique=True,  nullable=False)
    modified_by = db.Column(db.String(64), unique=False, nullable=True)
    os = db.Column(db.String(64), unique=False, nullable=True)
    site = db.Column(db.String(64), unique=False, nullable=True)
    cabinet = db.Column(db.String(64), unique=False, nullable=True)
    machine = db.Column(db.String(64), unique=False, nullable=True)
    description = db.Column(db.Text, unique=False, nullable=True)
    others = db.Column(db.Text, unique=False, nullable=True)   # store the variables for different business


class GroupParameter(MinModel, TimeUtilModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=False, nullable=False)
    value = db.Column(db.String(64), unique=False, nullable=False)
    others = db.Column(db.Text, unique=False, nullable=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True)
    group = db.relationship('Group', backref=db.backref('params', lazy=False), lazy=False)


class HostAccount(MinModel, TimeUtilModel):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=False, nullable=False)
    password = db.Column(db.String(64), unique=False, nullable=False)
    others = db.Column(db.Text, nullable=True)
    host_id = db.Column(db.Integer, db.ForeignKey('host.id'), nullable=True)
    host = db.relationship('Host', backref=db.backref('accounts', lazy=False), lazy=False)


class HostParameter(MinModel, TimeUtilModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=False, nullable=False)
    value = db.Column(db.String(64), unique=False, nullable=False)
    others = db.Column(db.Text, unique=False, nullable=True)
    host_id = db.Column(db.Integer, db.ForeignKey('host.id'), nullable=True)
    host = db.relationship('Host', backref=db.backref('params', lazy=False), lazy=False)

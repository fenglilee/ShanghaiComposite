#!/usr/bin/env python
# -*- coding:utf-8 -*-

from datetime import datetime
from aops.applications.database import db
from aops.applications.database.models.common import TimeUtilModel, MinModel


users_roles = db.Table('users_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)

roles_permissions = db.Table('roles_permissions',
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)

users_businesses = db.Table('users_businesses',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('business_id', db.Integer, db.ForeignKey('sys_config_business.id'), primary_key=True)
)


class User(MinModel, TimeUtilModel):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(64), unique=False, nullable=False)
    token = db.Column(db.String(64), nullable=True)
    realname = db.Column(db.String(64), unique=False, nullable=False)
    # business = db.Column(db.String(64), unique=False, nullable=False)
    businesses = db.relationship('SysConfigBusiness', secondary=users_businesses,
                                 backref=db.backref('users', lazy='dynamic'),
                                 lazy='dynamic')
    wechat = db.Column(db.String(64), unique=False, nullable=True)
    email = db.Column(db.String(128), unique=True, nullable=False)
    telephone = db.Column(db.String(24), unique=True, nullable=False)
    status = db.Column(db.Integer(), unique=False, nullable=False)
    modified_by = db.Column(db.String(64), unique=False, nullable=False)
    init_login = db.Column(db.Integer, unique=False, nullable=False, default=1)
    failure_time = db.Column(db.DateTime, unique=False, nullable=False, default=datetime.now())
    roles = db.relationship('Role', secondary=users_roles,
                            backref=db.backref('users', lazy='dynamic'),
                            lazy='dynamic')


class Role(MinModel, TimeUtilModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(100), nullable=True)
    created_user = db.Column(db.String(100), nullable=True)
    permissions = db.relationship('Permission', secondary=roles_permissions,
                                  backref=db.backref('roles', lazy='dynamic'),
                                  lazy='dynamic')


class Permission(MinModel, TimeUtilModel):
    id = db.Column(db.Integer, primary_key=True)
    permission = db.Column(db.String(80), unique=True, nullable=False)
    resource = db.Column(db.String(100), nullable=False)
    operation = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(150), nullable=True)

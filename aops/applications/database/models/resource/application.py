#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 2018/7/17 15:22
# @Author  : szf

from aops.applications.database import db
from aops.applications.database.models.resource.host import Host
from aops.applications.database.models.common import TimeUtilModel, MinModel

AppHost = db.Table('app_host',
    db.Column('host_id', db.Integer, db.ForeignKey('host.id'), primary_key=True),
    db.Column('app_id', db.Integer, db.ForeignKey('application.id'), primary_key=True)
)


# many <-> many: Application <-> Host
class Application(MinModel, TimeUtilModel):
    id = db.Column(db.Integer, primary_key=True)
    inst_id_cmdb = db.Column(db.Integer, nullable=True)
    instance_name = db.Column(db.String(100), unique=True, nullable=False)
    instance_description = db.Column(db.Text, unique=False, nullable=False)
    instance_status = db.Column(db.Integer, unique=False, nullable=False)     # 0: new , 1: modified, 2: published, 3: offline

    name = db.Column(db.String(64), unique=False, nullable=False)
    version = db.Column(db.String(64), unique=False, nullable=False)
    type = db.Column(db.String(64), unique=False, nullable=True)
    language = db.Column(db.String(64), unique=False, nullable=True)
    creator = db.Column(db.String(64), unique=False, nullable=True)
    sw_package_repository = db.Column(db.String(100), unique=False, nullable=False)
    cfg_file_repository = db.Column(db.String(100), unique=False, nullable=False)
    host_ips = db.Column(db.String(200), unique=False, nullable=True)
    hosts = db.relationship(Host, secondary=AppHost, lazy='subquery',
                            backref=db.backref('apps', lazy=True))

    business_group = db.Column(db.String(64), unique=False, nullable=False)
    publisher = db.Column(db.String(64), unique=False, nullable=True)
    publish_time = db.Column(db.DateTime, unique=False, nullable=True)
    others = db.Column(db.String(64), unique=False, nullable=True)


class AppParameter(MinModel, TimeUtilModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=False, nullable=False)
    value = db.Column(db.String(64), unique=False, nullable=False)
    others = db.Column(db.Text, unique=False, nullable=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=True)
    application = db.relationship('Application', backref=db.backref('parameters', lazy=False), lazy=False)

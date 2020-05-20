#!/usr/bin/env python
# -*- coding:utf-8 -*-
from aops.applications.database import db
from aops.applications.database.models.common import TimeUtilModel, MinModel


class Audit(MinModel, TimeUtilModel):
    __tablename__ = 'audit'
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(80), nullable=False)
    source_ip = db.Column(db.String(80), nullable=True)
    resource = db.Column(db.String(80), nullable=False)
    resource_id = db.Column(db.Integer(), nullable=True)
    operation = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    message = db.Column(db.String(80), nullable=True)

#!/usr/bin/env python
# -*- coding:utf-8 -*-
from aops.applications.database import db
from aops.applications.database.models.common import TimeUtilModel, MinModel


class DailyInspection(MinModel, TimeUtilModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    system_type = db.Column(db.String(64), nullable=False)
    target_ip = db.Column(db.Text, nullable=False)
    result = db.Column(db.String(64), nullable=True)
    description = db.Column(db.Text, nullable=True)
    item = db.Column(db.String(64), nullable=False)
    business_group = db.Column(db.String(64), nullable=False)
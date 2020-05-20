#!/usr/bin/env python
# -*- coding:utf-8 -*-
from aops.applications.database import db
from aops.applications.database.models.common import TimeUtilModel, MinModel


class Resource(MinModel, TimeUtilModel):
    id = db.Column(db.Integer, primary_key=True)
    resource_name = db.Column(db.String(80), unique=True, nullable=False)

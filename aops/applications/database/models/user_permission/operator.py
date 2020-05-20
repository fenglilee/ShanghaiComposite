#!/usr/bin/env python
# -*- coding:utf-8 -*-
from aops.applications.database import db
from aops.applications.database.models.common import TimeUtilModel, MinModel


class Operator(MinModel, TimeUtilModel):
    id = db.Column(db.Integer, primary_key=True)
    operator_name = db.Column(db.String(80), nullable=False)
    resource_name = db.Column(db.String(80), nullable=False)
#!/usr/bin/env python
# -*- coding:utf-8 -*-

from aops.applications.database import db
from aops.applications.database.models.common import TimeUtilModel, MinModel


class Todo(MinModel, TimeUtilModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    nickname = db.Column(db.String(80), unique=False, nullable=True)
    age = db.Column(db.Integer(), nullable=True)

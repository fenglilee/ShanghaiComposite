#!/usr/bin/env python
# -*- coding:utf-8 -*-
from aops.applications.database import db
from aops.applications.database.models.common import TimeUtilModel, MinModel


class RiskRepository(MinModel, TimeUtilModel):
    """
     Risk Repository
    """
    __tablename__ = 'risk_repository'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(120), nullable=False, unique=True)
    risk_level = db.Column(db.Integer(), nullable=False)
    comment = db.Column(db.String(120), nullable=False)
    creator = db.Column(db.String(60), nullable=False)
    business_group = db.Column(db.String(60), nullable=True)


class CommandWhiteList(MinModel, TimeUtilModel):
    """
    Command white list
    """
    __tablename__ = 'command_whitelist'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(120), nullable=False, unique=True)
    comment = db.Column(db.String(120), nullable=False)
    creator = db.Column(db.String(60), nullable=False)
    business_group = db.Column(db.String(60), nullable=True)

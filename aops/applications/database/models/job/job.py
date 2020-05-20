#!/usr/bin/env python
# -*- coding:utf-8 -*-
from aops.applications.database import db
from aops.applications.database.models.common import TimeUtilModel, MinModel


class Job(MinModel, TimeUtilModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    creator = db.Column(db.String(64), nullable=False)
    system_type = db.Column(db.String(64), nullable=False)
    target_ip = db.Column(db.Text, nullable=False)
    risk_level = db.Column(db.String(200), nullable=False)
    status = db.Column(db.Boolean(), nullable=False)
    execution_account = db.Column(db.String(200), nullable=False)
    scheduling = db.Column(db.Text, nullable=False)
    frequency = db.Column(db.Integer, nullable=False)
    success_rate = db.Column(db.Integer, nullable=False)
    job_type = db.Column(db.String(64), nullable=False)
    applications = db.Column(db.String(64), nullable=True)
    business_group = db.Column(db.String(64), nullable=False)
    task_id_list = db.Column(db.String(200), nullable=False)
    job_execution = db.relationship('JobExecution', backref='job', lazy=True)


class JobExecution(MinModel, TimeUtilModel):
    id = db.Column(db.Integer, primary_key=True)
    result = db.Column(db.String(64), nullable=True)

    timed_type = db.Column(db.String(64), nullable=True)
    timed_config = db.Column(db.String(64), nullable=True)
    executions_num = db.Column(db.Integer, nullable=True)           #重试次数
    last_time = db.Column(db.DateTime(), nullable=True)
    timed_expression = db.Column(db.String(200), nullable=True)     #周期 定时表达式
    timed_date = db.Column(db.String(200), nullable=True)           #定时 定时时间
    status = db.Column(db.Boolean(), default=True)                  #是否启动定时
    execution_id = db.Column(db.String(200), nullable=True)

    execution_type = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    job_type = db.Column(db.String(64), nullable=False)    # ordinary  update  quit  inspection
    creator = db.Column(db.String(64), nullable=False)
    execution_account = db.Column(db.String(200), nullable=False)
    target_ip = db.Column(db.Text, nullable=False)
    frequency = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=True)
    system_type = db.Column(db.String(64), nullable=False)
    risk_level = db.Column(db.String(200), nullable=False)
    scheduling = db.Column(db.Text, nullable=False)
    success_rate = db.Column(db.Integer, nullable=False)
    applications = db.Column(db.String(64), nullable=True)
    business_group = db.Column(db.String(64), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=True)














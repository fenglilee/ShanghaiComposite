#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 2018/7/18 10:01
# @Author  : szf


from aops.applications.database import db
from aops.applications.database.models.common import TimeUtilModel, MinModel
from aops.applications.database.models.system.user import User
from aops.applications.database.models.job.job import Job


# many <-> many: process <-> job ,manualJob <-> user
# one -> many: timed_process -> timed_config, process -> timed_process, process -> instant_process
processJob = db.Table('process_job',
    db.Column('job_id', db.Integer, db.ForeignKey('job.id'), primary_key=True),
    db.Column('process_id', db.Integer, db.ForeignKey('process.id'), primary_key=True)
)

# manualJobUser = db.Table('manual_job_user',
#     db.Column('manual_job_id', db.Integer, db.ForeignKey('manual_job.id'), primary_key=True),
#     db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
# )


class Process(MinModel, TimeUtilModel):
    """
    This is a template for process execution
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    creator = db.Column(db.String(64),unique=False, nullable=False)
    description = db.Column(db.Text, unique=False, nullable=False)
    risk_level = db.Column(db.String(200), unique=False, nullable=False)
    status = db.Column(db.Integer, unique=False, nullable=False)    # enabled/ disabled
    execution_account = db.Column(db.Integer, unique=False, nullable=False)
    success_rate = db.Column(db.Integer, nullable=False)
    has_manual_job = db.Column(db.Integer, unique=False, nullable=False)
    scheduling = db.Column(db.Text, nullable=False)     # copy jobs, including job/task configs.
    business_group = db.Column(db.String(64), nullable=False)
    jobs = db.relationship(Job, secondary=processJob, lazy='subquery',   #
                           backref=db.backref('processes', lazy=True))
    process_executions = db.relationship('ProcessExecution', backref='process', lazy=True)


class ProcessExecution(MinModel, TimeUtilModel):
    id = db.Column(db.Integer, primary_key=True)
    execution_type = db.Column(db.String(64), nullable=False)  # timed or instant
    timed_type = db.Column(db.String(64), nullable=True)  # cycle or timed
    timed_config = db.Column(db.String(64), nullable=True)
    timed_date = db.Column(db.String(64), nullable=True)
    timed_expression = db.Column(db.String(64), nullable=True)
    #####################################
    # Copied columns from Process Model
    ######################################
    name = db.Column(db.String(64), unique=True, nullable=False)
    creator = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text, nullable=True)
    risk_level = db.Column(db.String(200), unique=False, nullable=False)
    status = db.Column(db.Integer, unique=False, nullable=False)    # enabled/ disabled
    execution_account = db.Column(db.Integer, unique=False, nullable=False)
    success_rate = db.Column(db.Integer, nullable=False)
    has_manual_job = db.Column(db.Integer, unique=False, nullable=False)
    scheduling = db.Column(db.Text, nullable=False)     # including job/task configs.
    business_group = db.Column(db.String(64), nullable=False)

    process_id = db.Column(db.Integer, db.ForeignKey('process.id'), nullable=True)


# class ProcessExecutionRecord(MinModel, TimeUtilModel):
#     id = db.Column(db.Integer, primary_key=True)
#     execution_id = db.Column(db.String(64), nullable=False)
#     execution_type = db.Column(db.String(64), nullable=False)
#     timed_type = db.Column(db.String(64), nullable=True)
#     timed_config = db.Column(db.String(64), nullable=True)
#     timed_date = db.Column(db.String(64), nullable=True)
#     timed_expression = db.Column(db.String(64), nullable=True)
#     name = db.Column(db.String(64), nullable=False)
#     creator = db.Column(db.String(64), nullable=False)
#     executor = db.Column(db.String(64), nullable=False)
#     execution_status = db.Column(db.Integer, unique=False, nullable=False)   # new, executing, pause, stop, finish
#     result = db.Column(db.Integer, nullable=False)
#     start_time = db.Column(db.DateTime, nullable=False)
#     end_time = db.Column(db.DateTime, nullable=False)
#     scheduling = db.Column(db.Text, nullable=False)  # including job/task configs.
#     process_execution_id = db.Column(db.Integer, db.ForeignKey('process_execution.id'), nullable=True)


# class ManualJob(MinModel, TimeUtilModel):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(64), unique=True, nullable=False)
#     description = db.Column(db.Text, unique=False, nullable=False)
#     user_names = db.Column(db.String(100), unique=False, nullable=False)
#     users = db.relationship(User, secondary=manualJobUser, lazy='subquery',
#                             backref=db.backref('process_notifiers', lazy=True))
#     notify_by = db.Column(db.Integer, nullable=False)  # 0: 短信 1： 邮件
#
#     process_id = db.Column(db.Integer, db.ForeignKey('process.id'), nullable=True)
#     process = db.relationship(Process, backref=db.backref('manual_jobs', lazy=True))
#

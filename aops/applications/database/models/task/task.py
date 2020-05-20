#!/usr/bin/env python
# -*- coding:utf-8 -*-

from aops.applications.database import db
from aops.applications.database.models.common import TimeUtilModel, MinModel
from aops.applications.database.models.job import job

tasks_jobs = db.Table('tasks_jobs',
    db.Column('task_id', db.Integer, db.ForeignKey('task.id'), primary_key=True),
    db.Column('job_id', db.Integer, db.ForeignKey('job.id'), primary_key=True)
)


class Task(MinModel, TimeUtilModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    type = db.Column(db.String(64), nullable=False)
    language = db.Column(db.String(64), nullable=False)
    target_system = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text, nullable=False)
    risk_level = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(64), nullable=False)
    approver = db.Column(db.String(64), nullable=True)
    creator = db.Column(db.String(64), nullable=False)
    is_enable = db.Column(db.Boolean(), nullable=False, default=True)
    risk_statement = db.Column(db.Text, nullable=False)
    time_out = db.Column(db.Integer, nullable=False)
    business_group = db.Column(db.String(64), nullable=False)

    script = db.Column(db.Text, nullable=True)
    script_version = db.Column(db.String(64), nullable=True)
    project_id = db.Column(db.String(100), nullable=True)
    script_parameter = db.Column(db.Text, nullable=True)

    command = db.Column(db.Text, nullable=True)

    file_selection = db.Column(db.Text, nullable=True)
    target_directory = db.Column(db.Text, nullable=True)
    file_owner = db.Column(db.String(200), nullable=True)
    file_permission = db.Column(db.String(200), nullable=True)
    is_replace = db.Column(db.Boolean(), nullable=True)

    change_result = db.Column(db.String(64), nullable=True)
    task_reviews = db.relationship('TaskReview', backref='task', lazy=True)
    jobs = db.relationship('Job', secondary=tasks_jobs,
                                 backref=db.backref('tasks', lazy='dynamic'),
                                 lazy='dynamic')

class TaskReview(MinModel, TimeUtilModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    type = db.Column(db.String(64), nullable=False)
    language = db.Column(db.String(64), nullable=False)
    target_system = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(64), nullable=False)
    approver = db.Column(db.String(64), nullable=True)
    risk_level = db.Column(db.Integer, nullable=False)
    creator = db.Column(db.String(64), nullable=False)
    is_enable = db.Column(db.Boolean(), nullable=False, default=True)
    time_out = db.Column(db.Integer, nullable=False)
    risk_statement = db.Column(db.Text, nullable=False)
    business_group = db.Column(db.String(64), nullable=False)

    script = db.Column(db.Text, nullable=True)
    script_version = db.Column(db.String(64), nullable=True)
    project_id = db.Column(db.String(100), nullable=True)
    script_parameter = db.Column(db.Text, nullable=True)

    command = db.Column(db.Text, nullable=True)

    file_selection = db.Column(db.Text, nullable=True)
    target_directory = db.Column(db.Text, nullable=True)
    file_owner = db.Column(db.String(200), nullable=True)
    file_permission = db.Column(db.String(200), nullable=True)
    is_replace = db.Column(db.Boolean(), nullable=True)

    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    reviwe_records = db.relationship('ReviewRecord', backref='task_review', lazy=True)


class ReviewRecord(MinModel, TimeUtilModel):
    id = db.Column(db.Integer, nullable=True, primary_key=True)
    approver = db.Column(db.String(64), nullable=True)
    status = db.Column(db.String(16), default='pending')
    target_id = db.Column(db.Integer, db.ForeignKey('task_review.id'), nullable=False)
    approval_comments = db.Column(db.String(200), nullable=True)
    risk_level = db.Column(db.Integer, nullable=True)
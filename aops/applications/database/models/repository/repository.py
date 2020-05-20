#!/usr/bin/env python
# -*- coding:utf-8 -*-
from aops.applications.database import db
from aops.applications.database.models.common import TimeUtilModel, MinModel


reviews = db.Table('reviews',
                   db.Column('script_id', db.Integer, db.ForeignKey('repository_map.file_id'), primary_key=True),
                   db.Column('review_id', db.Integer, db.ForeignKey('file_review.id'), primary_key=True)
                   )


class RepositoryModel(MinModel, TimeUtilModel):
    """
     Repostiory, Maintain the correspondence between the platform and gitlab.
     scripts/configurations/applications
    """
    __tablename__ = 'repository_map'
    file_id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    name = db.Column(db.String(60), nullable=False)
    path = db.Column(db.String(120))
    full_path = db.Column(db.String(250), nullable=True)
    absolute_path = db.Column(db.String(250), nullable=False, unique=True)
    type = db.Column(db.String(10), default='blob')  # [blob: it's a file, tree: it's a directory]
    update_user = db.Column(db.String(60), nullable=False)
    project_id = db.Column(db.Integer(), nullable=True)
    project_name = db.Column(db.String(60), nullable=True)
    branch = db.Column(db.String(60))
    business_group = db.Column(db.String(60))
    risk_level = db.Column(db.Integer())
    comment = db.Column(db.String(120))
    script_versions = db.relationship('ScriptVersion', backref='script', lazy='dynamic')


class FileReview(MinModel, TimeUtilModel):
    """
    Record the operations, approval records
    """
    __tablename__ = 'file_review'
    id = db.Column(db.Integer, primary_key=True)  # 操作&审批记录
    merge_id = db.Column(db.Integer(), nullable=True)
    target_branch = db.Column(db.String(60), nullable=True)
    commit_sha = db.Column(db.String(120), nullable=True)
    submitter = db.Column(db.String(30), nullable=False)
    approver = db.Column(db.String(120), nullable=True)
    approval_comments = db.Column(db.String(250), nullable=True)
    status = db.Column(db.String(60), nullable=True, default='initial')  # status:[initial, pending, pass, not_pass]
    type = db.Column(db.String(60), nullable=False)  # type:[scripts, applications, configurations]
    business_group = db.Column(db.String(60))
    scripts = db.relationship('RepositoryModel', secondary=reviews, lazy=True,
                              backref=db.backref('file_reviews', lazy='dynamic'))


class ScriptVersion(MinModel, TimeUtilModel):
    """
    versions of the repository (script, config, package) at a time
    """
    __tablename__ = 'script_version'
    id = db.Column(db.Integer, primary_key=True)
    script_id = db.Column(db.Integer(), db.ForeignKey('repository_map.file_id'), nullable=False)
    commit_sha = db.Column(db.String(120), nullable=True)
    version = db.Column(db.String(120), nullable=True)

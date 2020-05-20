#!/usr/bin/env python
# -*- coding:utf-8 -*-

from .database import db
import aops.applications.database.models.job
import aops.applications.database.models.repository
from aops.applications.database.database import db
import aops.applications.database.models.task
import aops.applications.database.models.user_permission

from aops.applications.database.apis import application as app
from aops.applications.database.apis import message


##############################################
#
# Define interval executing tasks for Application
#
##############################################
def check_application_update_by_job_records(job_records):
    """ update application instance publish info by job records"""
    for record in job_records:
        if record.job_type == '应用发布':   # job is finished
            instance = app.update_publish_with_id()
            app.sync_instance_with_cmdb(instance.id)

        if record.job_type == '应用下线':
            instance = app.update_offline_with_id()
            app.sync_instance_with_cmdb(instance.id)


def check_application_update_by_process_records(process_records):
    """ update application instance publish info by process records"""
    for process_record in process_records:
        for job_record in process_record:
            if job_record.job_type == '应用发布':
                app.sync_instance_with_cmdb()
                app.update_publish_with_id()
            if job_record.job_type == '应用下线':
                app.update_offline_with_id()
                app.sync_instance_with_cmdb()


def check_manual_process(process_records):
    """
        check manual process and write a message into database,
        and somebody will be notified to execute a process again
    """
    for record in process_records:
        if record.job_type == 'manual' and record.execution_type == 2:    # pause

            #################################################################
            #  how to get notified users?
            #################################################################
            users = None
            data = {
                'classify': 1,    # 0: notification, 1:confirmation
                'risk_level': 0,  # 0:low, 1:middle, 2:high
                'content': 'This is a confirmation message to notify somebody to continue to execute a process',
                'status': 2,      # 0: confirmed, 1:non-confirmed, 2:unconfirmed,
                'users': users
            }
            message.create_message(**data)

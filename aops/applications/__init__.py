#!/usr/bin/env python
# -*- coding:utf-8 -*-
import gevent
import datetime
from aops.applications.database.apis.job.job_record import get_execution_record_list
from aops.applications.database.apis import process_execution_record
from aops.applications.database.apis.system.message.message import get_unsent_messages

from aops.applications.database import check_application_update_by_job_records,\
    check_application_update_by_process_records, check_manual_process

from aops.applications.lib.message_center import send_email, send_sms, send_wechat


POLL_INTERVAL = 60
DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 100   # I hope get all records one time


def register_polling_tasks(app):
    # gevent.spawn(fetch_job_records, app).start()
    # gevent.spawn(fetch_process_records, app).start()
    gevent.spawn(send_message, app).start()


def fetch_job_records(app):
    """ Fetch all job records from Scheduler """

    while True:
        try:
            with app.app_context():
                app.logger.info('Fetch the job records from Scheduler by interval')
                job_records = get_execution_record_list(DEFAULT_PAGE, DEFAULT_PER_PAGE)
                # other modules will be called to handle tasks according to the fetched job records
                check_application_update_by_job_records(job_records)
            gevent.sleep(POLL_INTERVAL)
        except Exception as e:
            app.logger.debug(e.message)
            break
        else:
            app.logger.info('Fetch the job records successfully')
        finally:
            app.logger.info('do something after fetching job records')


def fetch_process_records(app):
    """ Fetch all process records from Scheduler """

    while True:
        try:
            with app.app_context():
                app.logger.info('Fetch the process records from Scheduler by interval ...')
                # other modules will be called to handle tasks according to the fetched job records
                process_records = process_execution_record.get_execution_record_list(DEFAULT_PAGE, DEFAULT_PER_PAGE)
                check_application_update_by_process_records(process_records)
                check_manual_process(process_records)
            gevent.sleep(POLL_INTERVAL)
        except Exception as e:
            app.logger.debug(e.message)
            break
        else:
            app.logger.info('Fetch the process records successfully!!!')
        finally:
            app.logger.info('do something after fetching process records')


def send_message(app):
    """ Send message to notify users"""
    # 1. read message
    # 2. sent it to users
    # 3. set the message sent

    while True:
        try:
            with app.app_context():
                messages = get_unsent_messages()
                count = 0
                for message in messages:
                    app.logger.info('meessage object {}'.format(message))
                    users = message.users
                    if message.sent_by == 0:  # 短信
                        phone_list = [user.telephone for user in users]
                        # send_sms(phone_list=phone_list, content=message.content, send_time=datetime.datetime.now())
                        # message.update(is_sent=True)
                        count = count + 1

                    if message.sent_by == 1:  # wechat
                        wechat_list = [user.wechat for user in users]
                        send_wechat(receiver_list=wechat_list, message=message.content)
                        message.update(is_sent=True)
                        count = count + 1

                    if message.sent_by == 2:  # email
                        emails = [user.email for user in users]
                        send_email(content=message.content, receiver_list=emails, create_at=datetime.datetime.now())
                        message.update(is_sent=True)
                        count = count + 1
            gevent.sleep(POLL_INTERVAL)
        except Exception as e:
            app.logger.debug('send message ERROR {}'.format(e.message))
        else:
            app.logger.info('Send {} messages successfully!!!'.format(count))
        finally:
            app.logger.info('do something after send message')


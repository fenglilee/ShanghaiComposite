#!/usr/bin/env python
# -*- coding:utf-8 -*-
from aops.applications.common.scheduler_request import SchedulerApi
import pysftp
from flask import current_app as app
import json
import time
from aops.applications.database.apis.resource.host.host import get_host_ips_with_ids
import os
from aops.applications.exceptions.exception import ResourceNotFoundError, Error, NotFoundFtpFileError
import tempfile
import zipfile
import shutil


def get_time_str():
    return int(time.time())


def get_file_list_from_scheduler(args):
    target_ip = get_host_ips_with_ids([args.ip])
    if len(target_ip) > 0:
        target_ip = target_ip[0]
    else:
        raise ResourceNotFoundError("target_ip", args.ip)
    files = SchedulerApi('/v1/files/hosts?ip={}&path={}&execution_account={}&system_type={}'.
                         format(target_ip, args.path, args.execution_account, args.system_type)).get(timeout=30)
    return [item.update(name=os.path.basename(item.path)) for item in files]


def trigger_file_distributions(args):
    """
    carry out a instant　job
    Args:
        job_info: this instant job info

    Returns: execution id

    """
    target_ip = get_host_ips_with_ids(args.target_ip)
    app.logger.debug(target_ip)
    file_selection = []
    for f in args.full_path:
        file_selection.append(
            {
                "file": {"project_id": args.project_id, "full_path": f, "branch": "master", "type": 'blob'},
                "target_path": args.target_dest
            }
        )

    if args.replace:
        is_replace = 1
    else:
        is_replace = 0

    scheduling = {
            "name": "file_distributions",
            "file_owner": args.owner,
            "is_replace": is_replace,
            "file_permission": args.mode,
            "file_selection": json.dumps(file_selection),
            "type": 'file',
            "timestr": get_time_str(),
            "next": [
                {
                    "type": "end_success", "description": "", "is_warning": True,
                    "timestr": get_time_str() + 1,
                    "next": [],
                    "condition":{"type": "success", "value": ""}
                }
            ]
    }

    job_info = {
        "id": get_time_str(),
        "system_type": "linux",
        "frequency": "2",
        "name": "file_distributions",
        "description": "file_distributions description",
        "execution_account": args.execution_account,
        "business_group": args.business_group,
        "job_type": "distribution",
        "execution_type": "instant",
        "scheduling": json.dumps(scheduling),
        "target_ip": target_ip,
        "creator": args.creator
    }
    job_info = json.dumps(job_info)
    app.logger.debug(job_info)
    data = {
        'job_info': job_info
    }
    return SchedulerApi('/v1/instant_jobs/').post(data=data)


def get_download_record_list(page, per_page, creator=None):
    """
    Get all download record
    :return:
        download record list
    """
    return SchedulerApi('/v1/files?page={}&per_page={}&creator={}'.format(page, per_page, creator)).get()


def trigger_mul_download_files(args, business_group, creator, execution_account, system_type):
    target_ip = get_host_ips_with_ids(args.target_ip)
    # target_ip = ['10.111.2.40']
    if len(target_ip) == 0:
        raise ResourceNotFoundError('target_ip', ','.join(args.target_ip))
    app.logger.debug("path: {}".format(args.path))
    app.logger.debug("target_ip: {}".format(target_ip))
    data = {
        "target_ip": target_ip,
        "path": args.path,
        "business_group": business_group,
        "creator": creator,
        "execution_account": execution_account,
        "system_type": system_type
    }
    app.logger.debug("data: {}".format(data))
    return SchedulerApi('/v1/files/').post(json=data, headers={'Content-Type': 'application/json'})


def download_file_from_ftp(identifier):

    zip_file_dir = app.config.get('MUL_DOWNLOAD_CACHE')
    file_name = "{}.zip".format(identifier)
    zip_file_name = os.path.join(zip_file_dir, file_name)

    if not os.path.exists(zip_file_name):
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None

        host_address = app.config.get('FTP_SERVER')
        port = app.config.get('FTP_SERVER_PORT')
        username = app.config.get('FTP_SERVER_USER')
        private_key_path = app.config.get('PRIVATE_KEY_PATH')
        mul_download_data_dir = app.config.get('MUL_DOWNLOAD_DIR')
        local_tmp = tempfile.mkdtemp()
        conn = pysftp.Connection(host=host_address, username=username, port=port, cnopts=cnopts,
                                 private_key=private_key_path)

        remote_path = os.path.join(mul_download_data_dir, identifier)
        try:
            conn.get_d(remote_path, local_tmp, preserve_mtime=True)
        except IOError as e:
            raise NotFoundFtpFileError(host_address, remote_path, e.message)
        except OSError as e:
            raise Error(e.message)
        conn.close()

        with zipfile.ZipFile(zip_file_name, mode='w') as zipf:
            zipf.write(local_tmp)

        try:
            shutil.rmtree(local_tmp)
        except Exception as e:
            app.logger.errror("Delete sftp tmp file occur error: {}".format(e.message))
            raise Error("Delete sftp tmp file occur error: {}".format(e.message))

    return zip_file_name, file_name

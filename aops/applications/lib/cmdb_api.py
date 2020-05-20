#!/usr/bin/env python
# -*- coding:utf-8 -*-

import json
import datetime
from flask import current_app as app, jsonify
from aops.applications.common.cmdb_request import CmdbRequest
from aops.conf.cmdb_config import CMDB_BUSINESSES, SUPPLIER_ACCOUNT, CMDB_VERSION

"""
    User login for CMDB
"""


def get_host_list(business='LDDS'):
    """ GET host instance list by business, LDDS, CLOUD, ... """
    endpoint = "api/{}/inst/association/search/owner/{}/object/{}".\
        format(CMDB_VERSION, SUPPLIER_ACCOUNT, CMDB_BUSINESSES[business])
    data = {"page":{"sort":"-bk_inst_id"},"fields":{},"condition":{}}
    headers = {'Content-Type': 'application/json;charset=utf-8'}

    response = CmdbRequest(endpoint).post(data=json.dumps(data), headers=headers)

    if response['data'] and response['data']['count']:
        results, count = response['data']['info'], response['data']['count']
    else:
        results, count = None, 0

    app.logger.info('Get host list with business<{}> , count: {}, results: {}'.format(business, count, results))

    return results, count


def get_all_machine_list():
    endpoint = "api/{}/hosts/search".format(CMDB_VERSION)
    data = {"page": {}, "pattern": "", "ip": {}, "condition": []}
    headers = {'Content-Type': 'application/json;charset=utf-8'}
    response = CmdbRequest(endpoint).post(data=json.dumps(data), headers=headers)

    if response['data'] and response['data']['count']:
        results, count = response['data']['info'], response['data']['count']
    else:
        results, count = None, 0

    app.logger.info('Get all machine list, count: {}, results: {}'.format(count, results))

    return results


def get_host_with_name(host_name, business):
    """
    Args:
        host_name: "EC-C1-RZF2-VM6"
        business: LDDS, CLOUD
    Returns:
    """
    endpoint = "api/{}/inst/association/search/owner/{}/object/{}".\
        format(CMDB_VERSION, SUPPLIER_ACCOUNT, CMDB_BUSINESSES[business])
    data = {
        "page":{"start":0,"limit":10,"sort":"-bk_inst_id"},
        "fields":{},
        "condition":{
            "vm_private":[              #####################
                {"field":"bk_inst_name",
                 "operator":"$regex",
                 "value": host_name}]
        }
    }
    headers = {'Content-Type': 'application/json;charset=utf-8'}
    response = CmdbRequest(endpoint).post(data=json.dumps(data), headers=headers)
    if response['data'] and response['data']['count'] > 0:
        results, count = response['data']['info'], response['data']['count']
    else:
        results, count = None, 0
    app.logger.info('Get host with name <{}>, count: {}, results: {}'.format(host_name, count, results))

    return results, count


def get_host_with_lan_ip(lan_ip):
    pass


def create_app_if_not_exist(app_info):
    results, count = get_app_instance_with_name(app_info.instance_name)
    if count == 0:
        return create_app_instance(app_info)
    else:
        return results['data']['info'][0]['bk_inst_id']


def delete_app_if_exist(app_name):
    app_instances, count = get_app_instance_with_name(app_name)
    if app_instances and count == 1:
        endpoint = "api/{}/inst/{}/app_type/{}".format(CMDB_VERSION, SUPPLIER_ACCOUNT, app_instances[0]['bk_inst_id'])
        headers = {'Content-Type': 'application/json;charset=utf-8'}
        response = CmdbRequest(endpoint).delete(headers=headers)
        app.logger.info('Delete an app if exist from CMDB , result {}'.format(response))
        return response


def create_app_instance(app_info):
    """
    Args:
        app_info: app instance information in aops
    Returns:
        instance_id, 620
    """
    app.logger.info('create app instance into CMDB args: {}'.format(app_info))
    endpoint = "api/{}/inst/{}/app_type".format(CMDB_VERSION, SUPPLIER_ACCOUNT)
    data = {
        "type": app_info.type,
        "status": str(app_info.instance_status),
        "time": datetime.datetime.utcnow().date().strftime("%Y-%m-%d"),
        "bk_inst_name": app_info.instance_name,
        "memo": "",
        "dependence": "",
        "cn_inst_name": u"",
        "market": "",
        "package": "",
        "version": app_info.version,
        "conf": app_info.cfg_file_repository,
        "package_location": app_info.sw_package_repository
    }
    headers = {'Content-Type': 'application/json;charset=utf-8'}
    response = CmdbRequest(endpoint).post(data=json.dumps(data), headers=headers)
    app.logger.info('create app instance in CMDB result: {}'.format(response))

    return response['data']['bk_inst_id']


def update_app_instance(app_inst_id, app_info):
    """
    update an app instance
     Args:
         app_inst_id: the ID of app instance
         app_info: updated app instance information in aops
     Returns:
         True or False
     """
    app.logger.info('Update app instance into CMDB args: {}'.format(app_info))
    endpoint = "api/{}/inst/{}/app_type/{}".format(CMDB_VERSION, SUPPLIER_ACCOUNT, app_inst_id)
    data = {
        "type": str(app_info.type),   # a string
        "status": str(app_info.instance_status),
        "time": datetime.datetime.utcnow().date().strftime("%Y-%m-%d"),
        "bk_inst_name": app_info.instance_name,
        "memo": "",
        "dependence": "",
        "cn_inst_name": u"",
        "market": "",
        "package": "",
        "version": app_info.version,
        "conf": app_info.cfg_file_repository,
        "package_location": app_info.sw_package_repository
    }
    headers = {'Content-Type': 'application/json;charset=utf-8'}
    response = CmdbRequest(endpoint).put(data=json.dumps(data), headers=headers)
    app.logger.info('Update app instance in CMDB result: {}'.format(response))

    return response['data'] and 'success' == response['data']


def update_app_into_host(app_ids, host_id, business):
    """ Update host app info by app ids
    Args:
        app_ids: str , '1,3'
    Returns:
        success
    example:
        app_ids: 67
        host_id: 96
    """
    endpoint = "api/{}/inst/{}/{}/{}".\
        format(CMDB_VERSION, SUPPLIER_ACCOUNT, CMDB_BUSINESSES[business], host_id)
    data = {"app": app_ids}

    headers = {'Content-Type': 'application/json;charset=utf-8'}
    results = CmdbRequest(endpoint).put(data=json.dumps(data), headers=headers)

    app.logger.info('update app instance into host in CMDB, results: {}, app_ids: {}, host_id:{}'.\
                    format(results, app_ids, host_id))

    return results['data']


def get_app_instance_with_name(instance_name):
    """
    Example:
        instance_name: test_for_aops
    """
    url_template = "api/{}/inst/association/search/owner/{}/object/app_type"
    endpoint = url_template.format(CMDB_VERSION, SUPPLIER_ACCOUNT)
    data = {
        "condition":{
            "app_type":[{
                "field":"bk_inst_name",
                "operator":"$eq",
                "value": instance_name}
            ]},
        "fields":{},
        "page":{}
    }
    headers = {'Content-Type': 'application/json;charset=utf-8'}
    response = CmdbRequest(endpoint).post(data=json.dumps(data), headers=headers)
    if response['data'] and response['data']['count'] > 0:
        results, count = response['data']['info'], response['data']['count']
    else:
        results, count = None, 0
    app.logger.info('Get app instance with name <{}>, count: {}, results: {}'.format(instance_name, count, results))

    return results, count
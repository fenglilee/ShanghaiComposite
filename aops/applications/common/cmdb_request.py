#!/usr/bin/env python
# -*- coding:utf-8 -*-
from functools import wraps

import requests
import json
from flask import current_app as app
import aops.conf.cmdb_config as config
from aops.applications.exceptions.exception import CmdbError


def cmdb_error(func):
    @wraps(func)
    def warpper(self, data=None, headers=None, timeout=10):
        try:
            if func.func_name == "get":
                response = func(self, headers=headers, timeout=timeout)
            else:
                response = func(self, data=data, headers=headers, timeout=timeout)

        except Exception as e:
            raise CmdbError(e.message)
        if not response.ok:
            raise CmdbError(
                "CMDB's response code is {}, and reason is {}".format(response.status_code, response.reason))
        return json.loads(response.text)

    return warpper


class CmdbRequest(object):
    def __init__(self, endpoint):
        self.cmdb_schema = config.CMDB_HTTP_SCHEMA
        self.cmdb_host = config.CMDB_HOST
        self.cmdb_port = config.CMDB_PORT
        self.base_url = "{}://{}:{}".format(self.cmdb_schema, self.cmdb_host, self.cmdb_port)
        self.url = "{}/{}".format(self.base_url, endpoint.lstrip("/"))

    @cmdb_error
    def get(self, headers=None, params=None, timeout=10):
        return requests.get(self.url, headers=headers, params=params, timeout=timeout)

    @cmdb_error
    def post(self, data=None, headers=None, params=None, timeout=10):
        app.logger.debug('Post: {} with data {}'.format(self.url, data))
        res = requests.post(self.url, data=data, headers=headers, params=params, timeout=timeout)
        app.logger.debug('Post results: {}'.format(res))
        return res

    @cmdb_error
    def put(self, data=None, headers=None, params=None, timeout=10):
        app.logger.debug('Put: {} with data {}'.format(self.url, data))
        res = requests.put(self.url, data=data, headers=headers, params=params, timeout=timeout)
        app.logger.debug('Put results: {}'.format(res))
        return res

    def delete(self, data=None, headers=None, params=None, timeout=10):
        app.logger.debug('Delete: {} with data {}'.format(self.url, data))
        res = requests.delete(self.url, data=data, headers=headers, params=params, timeout=timeout)
        app.logger.debug('Delete results: {}'.format(res))
        return res
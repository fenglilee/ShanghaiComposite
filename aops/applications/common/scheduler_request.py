#!/usr/bin/env python
# -*- coding:utf-8 -*-
from functools import wraps

import requests
from flask import current_app as app

from aops.applications.exceptions.exception import SchedulerError


def sche_error(func):
    @wraps(func)
    def warpper(self, data=None, headers=None, params=None, json=None, timeout=10):
        try:
            if func.func_name == "get":
                response = func(self, headers=headers, params=params, timeout=timeout)
            elif func.func_name == "delete":
                response = func(self, headers=headers, timeout=timeout)
            else:
                response = func(self, data=data, headers=headers, json=json, timeout=timeout)

        except Exception as e:
            raise SchedulerError(e.message)
        if not response.ok:\
            raise SchedulerError(
                "Scheduler's response code is {}, and reason is {}".format(response.status_code, response.reason))
        try:
            import json
            return json.loads(response.text)
        except Exception as e:
            raise SchedulerError(
                "Scheduler's response code is {}, and reason is {}, msg: {}".format(response.status_code,
                                                                                    response.reason, e.message))

    return warpper


class SchedulerApi(object):
    def __init__(self, endpoint):
        self.sche_schema = app.config["SCHEDULER_HTTP_SCHEMA"]
        self.sche_host = app.config["SCHEDULER_HOST"]
        self.sche_port = app.config["SCHEDULER_PORT"]
        self.base_url = "{}://{}:{}".format(self.sche_schema, self.sche_host, self.sche_port)
        self.url = "{}/{}".format(self.base_url, endpoint.lstrip("/"))

    @sche_error
    def get(self, headers=None, params=None, timeout=10):
        return requests.get(self.url, headers=headers, params=params, timeout=timeout)

    @sche_error
    def post(self, data=None, headers=None, params=None, json=None, timeout=10):
        return requests.post(self.url, data=data, headers=headers, params=params, json=json, timeout=timeout)

    @sche_error
    def delete(self, headers=None, timeout=10):
        return requests.delete(self.url, headers=headers, timeout=timeout)
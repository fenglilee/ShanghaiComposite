#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 2018/7/13 13:11
# @Author  : szf

import json


class Dynamic(dict):
    def __init__(self, *args, **kw):
        super(Dynamic, self).__init__(*args, **kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value


def to_dynamic_dict(data):
    """
    convert a dict (or nested dict in list) to dynamic dict(s)
    args:
        data:  a dict or nested dict in list
    return:
        dynamic dict(s)
    """
    # add attribute access
    if type(data) == list:
        results = []
        for item in data:
            if type(item) == dict:
                results.append(Dynamic(item))
            else:
                results.append(item)

    elif type(data) == dict:
        results = Dynamic(data)

    else:
        results = data

    return results


def to_json_str(obj, encoding='unicode'):
    """
    convert a obj to a json string.
    args:
        obj: an python object
    return:
        a JSON string
    """
    return json.dumps(obj, encoding=encoding)


def to_object(json_str, encoding='unicode'):
    """

    args:
        json_str: a json string
    return:
        a python object
    """
    try:
        data = json.loads(json_str, encoding=encoding)
    except ValueError as e:
        raise ValueError(r"Parse pickle type string: '%s'" % e.message)

    return data


def parse_pickle_type(json_str, encode='unicode'):
    """
    Parse a json string into python list or dict, support for nest

    args:
        json_str:
    return:
    """
    try:
        data = json.loads(json_str, encoding=encode)
    except ValueError as e:
        raise ValueError(r"Parse pickle type string: '%s'" % e.message)

    # add attribute access
    if type(data) == list:
        results = []
        for item in data:
            if type(item) == dict:
                results.append(Dynamic(item))
            else:
                results.append(item)

    elif type(data) == dict:
        results = Dynamic(data)

    else:
        results = data

    return results


if __name__ == '__main__':
    data = parse_pickle_type("[{\"username\":\"user1\", \"password\":\"pwd1\"}]")
    print data[0].username

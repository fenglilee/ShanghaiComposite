#!/usr/bin/env python
# -*- coding:utf-8 -*-

from flask_restplus import Model, fields


time_util = Model('TimeUtil', {
    'created_at': fields.DateTime(required=False, description='Resource create time point'),
    'updated_at': fields.DateTime(required=False, description='Resource update time point'),
})

full_time_util = Model('TimeUtil', {
    'created_at': fields.DateTime(required=False, description='Resource create time point'),
    'updated_at': fields.DateTime(required=False, description='Resource update time point'),
    'deleted_at': fields.DateTime(required=False, description='Resource delete time point'),
    'is_deleted': fields.Boolean(required=False, default=False, description='Whether the resource was already deleted')
})


pagination_base_model = Model('TodoWithoutId', {
    'has_next': fields.Boolean(required=True, description='Whether have next page'),
    'has_prev': fields.Boolean(required=True, description='Whether have previous page'),
    'next_num': fields.Integer(required=True, description='Next page number'),
    'page': fields.Integer(required=True, description='Current page number'),
    'pages': fields.Integer(required=True, description='Total pages number'),
    'per_page': fields.Integer(required=True, description='The number of items in a page'),
    'prev_num': fields.Integer(required=True, description='Previous page num'),
    'total': fields.Integer(required=True, description='Total number of all items'),
})

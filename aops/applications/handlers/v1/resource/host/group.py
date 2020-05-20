#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 2018/7/4 14:16
# @Author  : szf

import datetime
from flask import current_app as app, jsonify, request
from flask_restplus import Namespace, Model, fields, reqparse, Resource, abort

from aops.applications.database.apis import group as group_api
from aops.applications.handlers.v1.common import time_util
from aops.applications.handlers.v1.resource.host.host import host_ip_model
from aops.applications.exceptions.exception import ResourceNotFoundError, ResourceAlreadyExistError


ns = Namespace('/v1/groups', description='Groups operations')

# define models
parameter_without_id_model = Model('ParameterWithoutID', {
   'name': fields.String(required=True, unique=True, description='The host parameter\'s name'),
   'value': fields.String(required=True, unique=True, description='The host parameter\'s value')

})

group_without_id_model = Model('groupWithoutID', {
    'pid': fields.Integer(readOnly=True, unique=False, description='The group\'s parent identifier'),
    'name': fields.String(required=True, unique=True, description='The group\'s name'),
    # business and host group maybe have different operations.
    #'business': fields.String(required=True, unique=False, description='The group\'s business'),

    #'is_read_only': fields.Integer(required=True, unique=False, description='The group can be modified or not'),
    'description': fields.String(required=True, unique=False, description='The group\'s description'),
    'params': fields.List(fields.Nested(parameter_without_id_model),
                          required=False, unique=False, description='The group\'s parameters'),
    'others': fields.String(required=False, unique=False, description='Other fields for extension')
})

group_model = group_without_id_model.clone('group', time_util, {
    'id': fields.Integer(readOnly=True, unique=True, description='The group\'s identifier'),
    'modified_by': fields.String(required=True, unique=False, description='The group\'s modified user'),
    'hosts': fields.List(fields.Nested(host_ip_model))
})

update_group_model = Model('updateGroupModel', {
    'name': fields.String(required=True, unique=True, description='The group\'s name'),
    # business and host group maybe have different operations.
    'description': fields.String(required=True, unique=False, description='The group\'s description'),
    'host_ids': fields.List(fields.String(required=False, description='The ip list of hosts in one group')),
    'params': fields.List(fields.Nested(parameter_without_id_model),
                          required=False, unique=False, description='The group\'s parameters')
})

tree_group_model = Model('treeGroupModel', {
    'tree_group': fields.String(description='The tree group')
})

# register models
ns.add_model(group_without_id_model.name, group_without_id_model)
ns.add_model(group_model.name, group_model)
ns.add_model(update_group_model.name, update_group_model)

# define parsers
group_without_id_parser = reqparse.RequestParser()
group_without_id_parser.add_argument('pid', required=True)
group_without_id_parser.add_argument('name', required=True)
group_without_id_parser.add_argument('params', type=list, location='json')
group_without_id_parser.add_argument('description', required=True)
group_without_id_parser.add_argument('host_ids', required=False, type=list, location='json')
# group_without_id_parser.add_argument('others', required=False)

group_parser = group_without_id_parser.copy()
group_parser.add_argument('id', type=int)

group_list_args = reqparse.RequestParser()
group_list_args.add_argument("group_name", type=str, location='args')
group_list_args.add_argument("business", type=str, location='args')
group_list_args.add_argument("fuzzy_query", type=str, location='args')

update_group_parser = reqparse.RequestParser()
update_group_parser.add_argument('name')
update_group_parser.add_argument('description')
update_group_parser.add_argument('host_ids', type=list, location='json')
update_group_parser.add_argument('params', type=list, location='json')
update_group_parser.add_argument('others')


@ns.route('/')
class Groups(Resource):
    """
    Show a list of all groups, and lets you POST to add a new group
    """

    @ns.doc('list_all_groups')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'Group list not found')
    @ns.expect(group_list_args)
    @ns.marshal_list_with(group_model)
    def get(self):
        """
        list all groups
        Returns:
             all groups
        """
        args = group_list_args.parse_args()
        app.logger.debug("Get group list's params are: {}".format(args))
        try:
            groups = group_api.get_group_list(group_name=args.group_name,
                                              business= args.business,
                                              fuzzy_query=args.fuzzy_query)
            app.logger.info("Get group list's result {}".format(groups))
        except ResourceNotFoundError as e:
            app.logger.error("group list can\'t be found with params: group_name={}, fuzzy_query={}". \
                             format(args.group_name, args.fuzzy_query))
            abort(404, e.message)

        return groups

    @ns.doc('create_group')
    @ns.expect(group_without_id_model)
    @ns.marshal_with(group_model, code=201)
    def post(self):
        """
        create a group items
        Returns:
            the new group items
        """
        args = group_parser.parse_args()
        args.update(created_at=datetime.datetime.now())
        app.logger.debug("Create group with params {}".format(args))

        try:
            created_group = group_api.create_group(args)
        except ResourceAlreadyExistError as e:
            app.logger.error('Create group {}'.format(e.message))
            abort(409, 'Already exist')

        app.logger.debug("Create group {}".format(created_group))

        return created_group, 201


@ns.route('/<int:identifier>')
@ns.param('identifier', 'The group\'s identifier')
class Group(Resource):
    """
    Show a single group, and let you query, delete or update it
    """

    @ns.doc('get_group')
    @ns.marshal_list_with(group_model)
    def get(self, identifier):
        """
        Get a group by identifier
        """
        app.logger.debug("Get group with identifier {}".format(identifier))
        try:
            group = group_api.get_group_with_id(identifier)
        except ResourceNotFoundError as e:
            app.logger.error("No group found with identifier {}".format(identifier))
            abort(404, e.message)

        app.logger.debug("get group {}".format(group))

        return group

    @ns.doc('delete_group')
    @ns.marshal_with(group_model, code=201)
    @ns.response(201, 'group deleted')
    def delete(self, identifier):
        """
        Delete a group by identifier
        """
        app.logger.debug("Delete group with identifier {}".format(identifier))
        try:
            group = group_api.delete_group_with_id(identifier)
            app.logger.info("Delete group {}".format(group))
        except ResourceNotFoundError as e:
            app.logger.error("No group found with identifier {}".format(identifier))
            abort(404, e.message)

        return group, 201

    @ns.doc('update_group')
    @ns.expect(update_group_model)
    @ns.marshal_with(group_model, code=201)
    def put(self, identifier):
        """Update a group given its identifier"""
        group_info = update_group_parser.parse_args()
        group_info.update(updated_at=datetime.datetime.now())
        app.logger.debug("update group with params {}".format(group_info))

        try:
            updated_group = group_api.update_group_with_id(identifier, group_info)
            app.logger.info("update group {}".format(updated_group))
        except ResourceNotFoundError as e:
            app.logger.error("No found updated group".format(e.message))
            abort(404, e.message)

        return updated_group, 201


# @ns.route('/<int:identifier>/subgroups')
# @ns.param('identifier', 'The parent group\'s identifier')
# class PGroup(Resource):
#     """
#     Get the children groups with some parent group's identifier
#     """
#
#     @ns.doc('get_children_group')
#     @ns.marshal_list_with(group_model)
#     def get(self, identifier):
#         """
#         Get children groups by parent group identifier
#         """
#         app.logger.debug("Get children groups with parent identifier {}".format(identifier))
#         try:
#             children_groups = group_api.get_groups_with_pid(identifier)
#         except ResourceNotFoundError as e:
#             app.logger.warning("No children group found with parent identifier {}".format(identifier))
#             return None
#         app.logger.debug("Get children group {}".format(children_groups))
#         return children_groups
#

@ns.route('/tree-groups')
class TreeGroup(Resource):
    """
    Get the tree groups
    """

    @ns.doc('get_tree_group')
    def get(self):
        """
        Get the tree groups
        """
        ROOT_PID = '0'
        business = request.cookies.get('BussinessGroup') or 'LDDS'
        app.logger.debug("Get tree groups, with root pid {}".format(ROOT_PID))
        try:
            tree_groups = group_api.get_tree_groups(ROOT_PID, business)
            app.logger.info("Get tree group {}".format(tree_groups))
        except ResourceNotFoundError as e:
            app.logger.warning("No tree group found !!", e.message)
            abort(404, e.message)

        result = jsonify(tree_groups)
        print result
        return result


@ns.route('/tree-ips')
class TreeIPGroup(Resource):
    """
    Get the tree groups
    """

    @ns.doc('get_tree_ips')
    def get(self):
        """
        Get the tree groups
        """
        business = request.cookies.get('BussinessGroup') or 'LDDS'
        app.logger.debug("Get tree ips")
        try:
            tree_ips = group_api.get_tree_ips('0', business)
            app.logger.info("Get tree ips {}".format(tree_ips))
        except ResourceNotFoundError as e:
            app.logger.warning("No tree ips found !!", e.message)
            abort(404, e.message)

        result = jsonify(tree_ips)

        return result
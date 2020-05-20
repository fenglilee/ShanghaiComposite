#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 2018/7/5 9:31
# @Author  : szf
import datetime
import json

from flask import current_app as app, request, session
from sqlalchemy import desc
from sqlalchemy.orm.exc import NoResultFound

from aops.applications.database.models.resource.host import Group, Host, GroupParameter as Parameter
from aops.applications.exceptions.exception import ResourceNotFoundError, ResourceAlreadyExistError
from aops.applications.common.scheduler_request import SchedulerApi


def _format_time(obj, key):
    """ to format the datetime obj"""
    fmt = '%Y-%m-%d %H:%M:%S'
    if obj.get(key) and type(obj[key]) == datetime.datetime:
        obj[key] = datetime.datetime.strftime(obj[key], fmt)

    return obj


def get_group_list(group_name=None, business=None, fuzzy_query=None):
    """
    Get all groups with filtered query
    Returns:
        group item list
    """
    results = []
    groups = Group.query.filter_by(is_deleted=False). \
        order_by(desc(Group.updated_at))

    # Precise query
    if group_name:
        groups = groups.filter(Group.name.like("%{}%".format(group_name)))

    if business:
        groups = groups.filter(Group.business.like("%{}%".format(business)))

    # Fuzzy query example
    if fuzzy_query:
        fuzzy_str = ''.join([Group.name, Group.type, Group.description])
        groups = groups.filter(fuzzy_str.like("%{}%".format(fuzzy_query)))
    for group in groups.all():
        results.append(_format_time(group.to_dict(), 'updated_at'))

    return results


def get_group_by_business(business):
    results = []
    groups = Group.query.filter_by(is_deleted=False, business=business). \
        order_by(desc(Group.updated_at))
    for group in groups.all():
        results.append(group.to_dict())

    return results


def create_group(args):
    """
    Create a group with args
    Args:
        args:dict which contain (pid, name, type, modified_by, host_ips, description, others)

    Returns:
        the created group
    """
    business = request.cookies.get('BussinessGroup')
    login_name = session.get('user_info').get('user')
    group = Group.query.filter_by(name=args.name, business=business, is_deleted=False).first()
    if group and not group.is_deleted:
        raise ResourceAlreadyExistError('Group')

    # rename the deleted group
    if group and group.is_deleted:
        group.name = args.name + '_is_deleted_' + str(group.id)

    data = {
        'pid': args.pid,
        'name': args.name,
        'type': 'group',
        'business': business,
        'is_read_only': 0,
        'modified_by': login_name,
        'description': args.description
    }
    if args.host_ids:    # args.host_ips shall be a list
        hosts = Host.query.filter(Host.id.in_(args.host_ids), Host.is_deleted.is_(False)).all()
        data.update({'hosts': hosts})
    if args.params:
        data.update({'params': [Parameter(**param) for param in args.params]})
    created_group = Group.create(**data)

    # sync hosts with scheduler to generate inventory.
    sync_updated_groups_with_scheduler({'updated': [created_group]})

    return created_group


def get_group_with_id(identifier):
    """
    Get a group with identifier
    Args:
        identifier: ID for group item

    Returns:
        Just the group item with this ID

    Raises:
          ResourceNotFoundError: group is not found
    """
    try:
        group = Group.query.filter_by(id=identifier, is_deleted=False).one()

    except NoResultFound:
        raise ResourceNotFoundError('group', identifier)
    return group


def get_groups_with_pid(parent_identifier):
    """
    Get children groups with parent identifier
    Args:
        parent_identifier: ID for parent group item
    Return:
        Just the list of children group items for the parent identifier

    """
    try:
        children_groups = Group.query.filter_by(pid=parent_identifier, is_deleted=False).all()
        for group in children_groups:
            group.host_ips = [host.identity_ip for host in group.hosts]
    except NoResultFound:
        raise ResourceNotFoundError('children_group', parent_identifier)

    return children_groups


def get_tree_groups(tree_pid, business):
    """ get tree groups"""

    app.logger.info('business Group in request cookies : {}'.format(business))
    nodes = get_group_list(business=business)
    if not nodes:
        return []
    host_nodes = traverse_nodes_host(nodes)
    return create_tree_data(host_nodes, tree_pid)


def get_tree_ips(tree_pid, business):
    app.logger.info('business Group in request cookies : {}'.format(business))
    nodes = get_group_list(business=business)
    if not nodes:
        return []
    ip_nodes = traverse_nodes_ip(nodes)
    return create_tree_data(ip_nodes, tree_pid)


def create_tree_data(nodes, tree_root_pid):
    """

    Returns:
        []
    """
    groups = {}
    for node in nodes:
        if node['pid'] not in groups.keys():
            groups[node['pid']] = []
        groups[node['pid']].append(node)
        if tree_root_pid and tree_root_pid == node['id']:
            tree_root_pid = node['pid']
    root_nodes = groups[tree_root_pid]
    groups[tree_root_pid] = None

    def traverse_tree_node_group(tree_node_group):
        for item in tree_node_group:
            if item['id'] in groups.keys():
                item['children'] = groups[item['id']]
                del groups[item['id']]
                traverse_tree_node_group(item['children'])

    traverse_tree_node_group(root_nodes)
    return root_nodes


def traverse_nodes_ip(nodes):
    traverse_nodes = []
    for node in nodes:
        traverse_nodes.append({'id': str(node['id']), 'pid': str(node['pid']), 'label': node['name']})
        if node['hosts']:
            for host in node['hosts']:
                if not host.is_deleted:
                    traverse_nodes.append({'id': str(node['id'])+ '_' + str(host.id), 'pid': str(node['id']), 'label': host.identity_ip})

    return traverse_nodes


def traverse_nodes_host(nodes):
    """ all nodes include group and host"""
    traverse_nodes = []
    for node in nodes:
        if node['hosts']:
            for host in node['hosts']:
                if host.is_deleted:
                    break
                host = _format_time(host.to_dict(), 'updated_at')
                host['accounts'] = [account.to_dict() for account in host['accounts']]
                host['params'] = [param.to_dict() for param in host['params']]
                # del host['groups']
                host.update({'id': str(node['id']) + '_' + str(host['id']), 'pid': str(node['id'])})
                traverse_nodes.append(host)
            del node['hosts']
        node['id'] = str(node['id'])
        node['pid'] = str(node['pid'])
        if node.get('params'):
            node['params'] = [param.to_dict() for param in node['params']]
        traverse_nodes.append(node)

    return traverse_nodes


def delete_group_with_id(identifier):
    """
    Delete a group with identifier
    Args:
        identifier: ID for group item

    Returns:
        Just the group item with this ID.
    """
    try:
        group = Group.query.filter_by(id=identifier, is_deleted=False).one()
    except ResourceNotFoundError as e:
        raise ResourceNotFoundError('Group', e.message)
    deleted_group = group.update(is_deleted=True, deleted_at=datetime.datetime.now())
    # deleted_group.host_ips = [host.identity_ip for host in deleted_group.hosts]

    # sync hosts with scheduler to generate inventory.
    sync_updated_groups_with_scheduler({'deleted': [deleted_group]})

    return deleted_group


def update_group_with_id(identifier, args):
    """
    Update a group with identifier
    Args:
        identifier: ID for group item
        args: update group with this info

    Returns:
        Just the group item with this ID.
    """

    login_name = session.get('user_info').get('user')
    group = Group.query.filter_by(id=identifier, is_deleted=False).first()
    if group is None:
        raise ResourceNotFoundError('group', identifier)

    data = {
        'name': args.name,
        'description': args.description,
        'modified_by': login_name
    }
    if args.host_ids:
        hosts = Host.query.filter(Host.id.in_(args.host_ids), Host.is_deleted.is_(False)).all()
        data.update({'hosts': hosts})
    if args.params:
        data.update({'params': [Parameter(**param) for param in args.params]})

    updated_group = group.update(**data)

    # sync hosts with scheduler to generate inventory.
    sync_updated_groups_with_scheduler({'updated': [updated_group]})

    return updated_group


def init_business_groups(businesses):
    """ init default groups for AOPS, that is, business group
        Args:
            businesses: A list ,[{name:'business_name': description: 'business_description}, ...]
    """
    login_name = session.get('user_info').get('user')
    basic_info = {
        'pid': 0,
        'type': 'business',
        'is_read_only': 1,
        'modified_by': login_name,
        'description': 'This is a DEFAULT business Group'
    }
    groups = []
    for business in businesses:
        group_info = basic_info.copy()
        group_info.update({'name': business.name, 'business': business.name})
        groups.append(group_info)

    initial_groups = []
    for args in groups:
        group = Group.query.filter_by(name=args['name']).first()
        if group:
           app.logger.info(u"Group {} already exists".format(group.name))
        else:
            group = Group.create(**args)
            initial_groups.append(group.to_dict())
    return initial_groups


def delete_business_groups(businesses):
    """delete business groups by business name """
    deleted_bs_groups = []
    names = [business.name for business in businesses]
    bs_groups = Group.query.filter(Group.name.in_(names), Group.type == 'business', Group.is_deleted.is_(False)).all()
    for bs_group in bs_groups:
        deleted_at = datetime.datetime.now()
        rename = bs_group.name + '_' + datetime.datetime.strftime(deleted_at, '%Y-%m-%d_%H:%M:%S')
        group = bs_group.update(name=rename, deleted_at=deleted_at, is_deleted=True)  # soft delete
        deleted_bs_groups.append(group)

    return deleted_bs_groups


def init_aops_all_host_group(business):
    """ create a ALL_HOST group for Aops"""
    login_name = session.get('user_info').get('user')
    ALL_HOST = 'ALL_HOST'
    data = {
        'type': 'group',
        'name': ALL_HOST,
        'business': business,
        'is_read_only': 1,
        'modified_by': login_name,
        'description': 'This is a DEFAULT business Group'
    }
    pgroup = Group.query.filter_by(name=business, type='business', business=business).first()
    data.update({'pid': pgroup.id})

    group = Group.query.filter_by(name=ALL_HOST, type='group', business=business).first()
    if group:
        app.logger.info(u"Group {} already exists".format(group.name))
    else:
        group = Group.create(**data)
    return group


def init_cmdb_default_groups():
    """ init default groups for CMDB"""
    group = Group.query.filter_by(name='ALL_HOSTS', type='group').first()
    if group and not group.is_deleted:
        return group

    data = {
        'pid': 0,
        'name': 'ALL',
        'type': 'group',
        'business': '-',
        'is_read_only': 1,
        'modified_by': '-',
        'description': 'This is a DEFAULT Host Group'
    }
    hosts = Host.query.filter_by(is_deleted=False).all()

    data.update({'hosts': hosts})
    return Group.create(**data)


def _init_all_host_group(hosts, host_types, OSs, sites, cabinets):
    basic = {
        'type': 'group',
        'business': '-',
        'is_read_only': 1,
        'modified_by': 'Admin',
        'description': 'This is DEFAULT group'
    }
    data = basic.update({      # All host
        'pid': 0,
        'name': 'ALL HOST'
    })
    level_1 = Group.create(**data)

    level_2 = []
    for type in host_types:
        data = basic.update({
            'pid': level_1.id,
            'name': type,
            'description': 'This is DEFAULT group'
        })
        level_2.append(Group.create(**data))

    level_3 = []
    for group in level_2:
        for os in OSs:
            data = basic.update({
                'pid': group.id,
                'name': os
            })
            level_3.append(Group.create(**data))

    level_4 = []
    for group in level_3:
        for site in sites:
            data = basic.update({
                'pid': group.id,
                'name': site
            })
            level_4.append(Group.create(**data))

    level_5 = []
    for group in level_4:
        for cabinet in cabinets:
            data = basic.update({
                'pid': group.id,
                ''
                'name': cabinet
            })
            level_5.append(Group.create(**data))

    # map hosts for level_5 (host group)


def add_host_into_group(tree_root_id, hosts):
    pass


def update_all_host_group():
    """ update all host group after sync host again"""
    pass


def _get_group_classify(hosts):
    results = {
        'site': [],
        'cabinet': [],
        'xxs': [],
        'qs': [],
        'host_type': ['Virtual', 'Physical'],
        'os': ['Linux', 'Windows']
    }

    for host in hosts:
        if host.site:
            results['site'].append(host.site)
        if host.cabinet:
            results['cabinet'].append(host.cabinet)
        others = json.loads(host.others)
        for item in others:
            if item['key_en'] == 'xxs':
                results['xxs'].append(item['value'])
            elif item['key_en'] == 'qs':
                results['qs'].append(item['value'])
    for key, value in results.items():
        results[key] = list(set(value))

    return results


def _is_target_type(host, type):
    return type == 'Virtual' and host.machine


def _is_target_os(host, os_type):
    return 'windows' in host.os.lower()


def _is_target_site(host, site):
    pass


def _is_target_cabinet(host, site):
    pass


def _is_target_qs(host, site):
    pass


def _is_target_xxs(host, site):
    pass


#############################################
#
# ########################################
# #
# # SYNC HOSTS with Scheduler related APIs
# #
# ########################################
#
#############################################
def sync_all_groups_with_scheduler(business):

    tree_pid = '0'
    nodes = get_group_list(business=business)
    host_nodes = traverse_nodes_host(nodes)
    inventory_nodes = _prepare_inventory_group(host_nodes)
    tree_group = create_tree_data(inventory_nodes, tree_pid)

    data = {'tree-group': tree_group}
    app.logger.info('Post all inventory hosts to scheduler, args: {}'.format(data))
    headers = {'Content-Type': 'application/json;charset=utf-8'}
    response = SchedulerApi('/v1/inventories/generate-hosts/').post(data=json.dumps(data), headers=headers)
    app.logger.info('Post tree group hosts to scheduler, result: {}'.format(response))

    return tree_group


def sync_updated_groups_with_scheduler(nodes):
    """ sync updated tree groups when one group is updated/deleted/added
    Args:
        nodes: {deleted:[0]/None, updated:[0]/None}
    """
    tree_pid = '0'
    if nodes.get('deleted'):
        deleted_node = nodes.get('deleted')[0]
        node = attach_state(deleted_node, is_deleted=1)
        node.hosts = attach_states(node.hosts, is_deleted=1)
    if nodes.get('updated'):
        deleted_node = nodes.get('updated')[0]
        node = attach_state(deleted_node, is_updated=1)
        node.hosts = attach_states(node.hosts, is_updated=1)

    if not node:
        return []
    tree_group = _generate_tree_group(tree_pid, [node])

    data = {'tree-group': tree_group}
    app.logger.info('Post updated inventory hosts to scheduler, args: {}'.format(data))
    headers = {'Content-Type': 'application/json;charset=utf-8'}
    response = SchedulerApi('/v1/inventories/update-hosts/').post(data=json.dumps(data), headers=headers)
    app.logger.info('Post tree group hosts to scheduler, result: {}'.format(response))

    return tree_group


def sync_updated_hosts_with_scheduler(results):
    """sync updated tree hosts when import host accounts, host information, sync cmdb or modify host'"""
    tree_groups = []
    tree_pid = '0'
    updated_hosts = []
    deleted_hosts = []
    if results.get('updated'):
        updated_hosts.extend(results.get('updated'))
    if results.get('added'):
        updated_hosts.extend(results.get('added'))
    if results.get('deleted'):
        deleted_hosts.extend(results.get('deleted'))

    if updated_hosts:
        groups = get_related_groups_with_hosts(updated_hosts, is_updated=1)
        # updated_hosts = attach_states(updated_hosts, is_updated=1)
        updated_tree_group = _generate_tree_group(tree_pid, groups)
        tree_groups.extend(updated_tree_group)

    if deleted_hosts:
        # deleted_hosts = attach_states(deleted_hosts, is_deleted=1)
        groups = get_related_groups_with_hosts(updated_hosts, is_deleted=1)
        deleted_tree_group = _generate_tree_group(tree_pid, groups)
        tree_groups.extend(deleted_tree_group)

    data = {'tree-group': tree_groups}
    app.logger.info('Post updated inventory hosts to scheduler, args: {}'.format(data))
    headers = {'Content-Type': 'application/json;charset=utf-8'}
    response = SchedulerApi('/v1/inventories/update-hosts/').post(data=json.dumps(data), headers=headers)
    app.logger.info('Post tree group hosts to scheduler, result: {}'.format(response))

    return tree_groups


def _generate_tree_group(tree_pid, groups):
    nodes = get_parent_tree(groups)
    host_nodes = traverse_nodes_host(nodes)
    inventory_nodes = _prepare_inventory_group(host_nodes)
    tree_group = create_tree_data(inventory_nodes, tree_pid)
    return tree_group


def get_related_groups_with_hosts(hosts, is_updated=None, is_deleted=None):
    """ get the changed groups by hosts"""
    name_group_map = {}

    for host in hosts:
        for group in host.groups:
            if not group.is_deleted and group.name not in name_group_map.keys():
                # group.hosts = group.__getattribute__('hosts')     ### lazy load for hosts

                # add state for the target host in group
                if is_deleted:
                    group.hosts = attach_states(group.hosts, target_id=host.id, is_deleted=1)
                if is_updated:
                    group.hosts = attach_states(group.hosts, target_id=host.id, is_updated=1)
                name_group_map[group.name] = group
    return name_group_map.values()


def get_parent_tree(nodes):
    """get all parent nodes tree by given nodes"""
    app.logger.debug('Get parent tree, args: {}'.format(nodes))

    def get_parent_nodes(cur_node, result={}):
        """ get a branch from current node to root node"""
        if cur_node.pid == 0:
            return
        else:
            parent_node = get_group_with_id(cur_node.pid)

            if not result.get(parent_node.name):
                result[parent_node.name] = parent_node
            get_parent_nodes(parent_node, result)

    result = {}
    for node in nodes:
        get_parent_nodes(node, result)
        if not result.get(node.name):
            result[node.name] = node

    parent_nodes = []
    for key, value in result.items():
        parent_nodes.append(value.to_dict())

    app.logger.debug('Get parent tree, results: {}'.format(parent_nodes))
    return parent_nodes


def _prepare_inventory_group(nodes):
    app.logger.debug('Prepare inventory groups, args: {}'.format(nodes))
    group_key_map = {
        'id': 'id',
        'pid': 'pid',
        'name': 'name',
        'business': 'business'
    }

    inventory_nodes = []
    for node in nodes:
        if node['type'] == 'host':    # 主机信息
            inventory_node = _prepare_inventory_host(node)
            inventory_nodes.append(inventory_node)
        else:                         # 主机组信息
            inventory_node = {}
            for key1, key2 in group_key_map.items():
                inventory_node[key2] = node[key1]
            inventory_node['params'] = _convert_params(node.get('params'))
            if 'is_update' in node.keys():
                inventory_node.update({'is_update': node['is_update']})
            if 'is_delete' in node.keys():
                inventory_node.update({'is_delete': node['is_delete']})
            inventory_nodes.append(inventory_node)
    app.logger.debug('Prepare inventory groups, results: {}'.format(inventory_nodes))

    return inventory_nodes


def _convert_params(params):
    """ convert params list into dict"""
    convert_params = {}
    if params:
        for param in params:
            convert_params[param['name']] = param['value']
    return convert_params


def _prepare_inventory_host(host):
    # app.logger.debug('Prepare inventory hosts, args: {}'.format(host))
    host_key_map = {
        'id': 'id',
        'pid': 'pid',
        'name': 'name',
        'business': 'business',
        'identity_ip': 'ip',
        'os': 'os'
    }
    if not host:
        return {}
    inventory_host = {}
    for key1, key2 in host_key_map.items():
        inventory_host[key2] = host[key1]

    if host.get('os'):
        inventory_host['os'] = 'windows' if 'windows' in host['os'] else 'linux'
    if host.get('params'):
        params = {}
        for param in host['params']:
            params[param['name']] = param['value']
        inventory_host['params'] = params
    else:
        inventory_host['params'] = {}

    inventory_host['accounts'] = [{'username': account['username'], 'password': account['password']}
                                  for account in host['accounts']] if host.get('accounts') else []

    inventory_host.update({'port': '2222'})  # hard code
    if 'is_delete' in host.keys():
        inventory_host.update({'is_delete': host['is_delete']})  # hard code, different is_deleted
    if 'is_update' in host.keys():
        inventory_host.update({'is_update': host['is_update']})  # hard code

    # app.logger.debug('Prepare inventory host, result: {}'.format(inventory_host))

    return inventory_host


def attach_state(obj, is_updated=None, is_deleted=None):
    if is_updated:
        obj.is_update = 1
        obj.is_delete = 0
    if is_deleted:
        obj.is_update = 0
        obj.is_delete = 1

    return obj


def attach_states(objs, target_id=None, is_updated=None, is_deleted=None):
    results = []
    if target_id:
        for obj in objs:
            if obj.id == target_id:
                obj = attach_state(obj, is_updated=is_updated, is_deleted=is_deleted)
                results.append(obj)
    else:
        for obj in objs:
            obj = attach_state(obj, is_updated=is_updated, is_deleted=is_deleted)
            results.append(obj)

    return results

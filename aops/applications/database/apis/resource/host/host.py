#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 18-7-4 上午10:38
# @Author  : szf
from flask import current_app as app, request, session
import json
import datetime
from sqlalchemy import desc
from sqlalchemy.orm.exc import NoResultFound

from aops.applications.database.models import Host
from aops.applications.database.models import Group
from aops.applications.database.models import HostAccount, HostParameter
from aops.applications.database.apis.resource.host.group import get_groups_with_pid,\
    init_aops_all_host_group, sync_updated_hosts_with_scheduler, sync_all_groups_with_scheduler
from aops.applications.exceptions.exception import ResourceNotFoundError, ResourceAlreadyExistError
from aops.conf.cmdb_config import BUSINESS_HOST_KEY_MAP, BUSINESS_HOST_KEYNAME_MAP, HOST_ACCOUNT_KEY_MAP
from aops.applications.common.scheduler_request import SchedulerApi
from aops.applications.lib.cmdb_api import get_host_list


def get_hosts_list(business=None, fuzzy_query=None):
    """
    Get all hosts items with query filter
    Returns:
        host list
    """
    """
    Get all hosts items with query filter
    Returns:
        host list
    """
    hosts = Host.query.filter_by(is_deleted=False). \
        order_by(desc(Host.updated_at))

    # Precise query
    if business:
        hosts = hosts.filter(Host.business.like("%{}%".format(business)))

    # Fuzzy query example
    if fuzzy_query:
        fuzzy_str = ''.join([Host.name, Host.identity_ip, Host.description])
        hosts = hosts.filter(fuzzy_str.like("%{}%".format(fuzzy_query)))

    return hosts.all()


def create_host(args):
    """
    Create a host with args
    Args:
        args:dict which contain (host_name, host_location,host_ip, host_description)

    Returns:
        the created host
    """
    host = Host.query.filter_by(name=args.name).first()
    if host and not host.is_deleted:
        raise ResourceAlreadyExistError('Host')

    if host and host.is_deleted:
        host.name = args.name + '_is_deleted_' + str(host.id)

    accounts = [HostAccount(**account) for account in args.accounts] if args.accounts else []
    params = [HostParameter(**param) for param in args.params] if args.params else []
    host = Host.create(name=args.name,
                       business=args.business,
                       modified_by=args.modified_by,
                       identity_ip=args.identity_ip,
                       os=args.os,
                       description=args.description,
                       accounts=accounts,
                       params=params,
                       others=args.others)

    return host.to_dict()


def get_host_with_id(identifier):
    """
    Get a host with identifier
    Args:
        identifier: ID for host item

    Returns:
        Just the host item with this ID

    Raises:
          ResourceNotFoundError: host is not found
    """
    try:
        host = Host.query.filter_by(id=identifier, is_deleted=False).one()
        host.others = json.loads(host.others) if host.others else None
    except NoResultFound:
        raise ResourceNotFoundError('Host', identifier)
    return host.to_dict()


def get_host_ips_with_business(business):
    hosts = Host.query.filter_by(is_deleted=False, business=business).all()
    return [{'id': host.id, 'identity_ip': host.identity_ip} for host in hosts]


def get_host_ips_with_ids(ids):
    """ get host ips by the list of group id or host id
    Args:
        ids: the list of group id ('1'), or host id ('1_1')
    """
    host_ips = []
    group_ids = []
    host_ids = []
    for id in ids:
        if '_' not in str(id):  # query group
            group_ids.append(int(id))
        elif '_' in str(id):   # query host
            host_ids.append(str(id).split('_')[1])

    for id in group_ids:
        group = Group.query.filter_by(id=int(id), is_deleted=False).first()
        get_tree_host_ips(group, host_ips)

    hosts = get_hosts_with_ids(host_ids)
    for host in hosts:
        if host.identity_ip:
            host_ips.append(host.identity_ip)

    return list(set(host_ips))


def get_tree_host_ips(node, ips=[]):
    """
    Args:
     node: group node
     host_ids: store the id list
    """
    if node.hosts:
        ips.extend([host.identity_ip for host in node.hosts if not host.is_deleted])
    else:
        children = get_groups_with_pid(node.id)
        for child in children:
            get_tree_host_ips(child, ips)


def get_host_with_ip(identity_ip):
    """
    Get the host with the given identity_ip.
    Args:
        identity_ip: the host identity ip
    Return:
        The host items with ID
    """
    try:
        host = Host.query.filter_by(dentity_ip=identity_ip, is_deleted=False).first()
    except NoResultFound:
        raise ResourceNotFoundError('Host ips ', identity_ip)
    return host


def get_hosts_with_ids(ids):
    """
    Get the hosts with the given ids list.
    Args:
        ids: the list of host identity ips
    Return:
        The host items with ID
    """
    try:
        hosts = Host.query.filter(Host.id.in_(ids), Host.is_deleted.is_(False)).all()
    except NoResultFound:
        raise ResourceNotFoundError('Host ids ', ids)
    return hosts


def delete_host_with_id(identifier):
    """
    Delete a host with identifier
    Args:
        identifier: ID for host item

    Returns:
        Just the host item with this ID.
    """
    return Host.soft_delete_by(id=identifier)


def update_host_with_id(identifier, host_info):
    """
    Update a host with identifier
    Args:
        identifier: ID for host item
        host_info: update host with this info

    Returns:
        Just the host item with this ID.
    """
    host = Host.query.filter_by(id=identifier, is_deleted=False).first()
    if host is None:
        raise ResourceNotFoundError('Host', identifier)

    accounts = [HostAccount(**account) for account in host_info['accounts']] if host_info['accounts'] else []
    params = [HostParameter(**param) for param in host_info['params']] if host_info['params'] else []
    host_info.update(id=identifier, accounts=accounts,
                     params=params, updated_at=datetime.datetime.now())

    updated_host = host.update(**host_info)

    # sync hosts with scheduler to generate inventory.
    sync_updated_hosts_with_scheduler({'updated': [host]})

    return updated_host


########################################
#
# SYNC HOSTS with CMDB related APIs
#
########################################
def sync_host_accounts(host_accounts, business):
    """"
    Sync hosts' accounts with db

    Args:
        host_acounts: a host account list , include host_name, ip, username, password
    """
    accounts = _prepare_host_accounts(host_accounts)
    host_names = [account['host_name'] for account in accounts]
    account_map = {}
    for account in accounts:
        host_name = account['host_name']
        if host_name not in account_map:
            account_map[host_name] = []
        account_map[host_name].append(HostAccount(username=account['username'],
                                                  password=account['password']))

    hosts = Host.query.filter(Host.name.in_(host_names), Host.business == business).all()
    updated_hosts = []
    for host in hosts:
        for account in host.accounts:
            account.delete()
        updated_host = host.update(accounts=account_map[host.name], updated_at=datetime.datetime.now())
        updated_hosts.append(updated_host)

    # sync hosts with scheduler to generate inventory.
    sync_updated_hosts_with_scheduler({'updated': updated_hosts})

    return [{'id': host.id, 'name': host.name, 'identity_ip': host.identity_ip} for host in updated_hosts]


def _prepare_host_accounts(accounts):
    """ prepare host accounts
    Args:
        accounts: a list including the total information of host,
        (Date, Time, Hostname, IP_Address, Account, LastPassword, Password, Status )
    """
    results = []

    for account in accounts:
        item = {}
        for key, value in account.items():
            if key in HOST_ACCOUNT_KEY_MAP:
                item[HOST_ACCOUNT_KEY_MAP[key]] = value
        if item:
            results.append(item)
    app.logger.info('prepare host accounts ===> {}'.format(results))
    return results


def sync_hosts_info(file_hosts_info, business, login_name):
    """sync host information with db ,except accounts, according to BUSINESS GROUP"""
    file_hosts_info = _prepare_host_info(file_hosts_info, business, login_name)
    results = _sync_host_with_db(file_hosts_info, business)

    # relate all hosts with all host group
    if results['added'] or results['updated']:
        hosts = []
        hosts.extend(results['added'])
        hosts.extend(results['updated'])
        group = init_aops_all_host_group(business)
        group.update(hosts=hosts)

    # sync hosts with scheduler to generate inventory.
    sync_all_groups_with_scheduler(business)

    return _load_host_others(results)


def sync_host_with_cmdb(business, login_name):
    """ sync hosts with cmdb by RESTFUL API"""
    results, count = get_host_list(business)
    hosts_info = parse_hosts_info_from_cmdb(results, business)
    hosts = _prepare_host_info(hosts_info, business, login_name)
    app.logger.info('Hosts from cmdb: {}, {}'.format(hosts, len(hosts)))
    results = _sync_host_with_db(hosts, business)

    # add the host into ALL_HOST_<business> group
    if results['added'] or results['updated']:
        hosts = []
        hosts.extend(results['added'])
        hosts.extend(results['updated'])
        group = init_aops_all_host_group(business)
        group.update(hosts=hosts)

    # sync hosts with scheduler to generate inventory.
    sync_all_groups_with_scheduler(business)

    return _load_host_others(results)


def _load_host_others(sync_hosts):
    results = {}
    for key, hosts in sync_hosts.items():
        results[key] = []
        for host in hosts:
            host = host.to_dict()
            host['others'] = json.loads(host['others'])
            results[key].append(host)

    return results


def parse_hosts_info_from_cmdb(hosts, business):
    """ remove some host info from RESTFUL API"""
    def get_inst_names(value):
        if type(value) == list:
            return ','.join([item['bk_inst_name'] for item in value])
        elif type(value) == unicode or type(value) == int:
            return value

    keys = BUSINESS_HOST_KEYNAME_MAP.get(business, None)
    if not keys:
        return []

    results = []
    for host in hosts:
        tmp = {}
        for key, value in host.items():
            if key in keys:
                tmp[key] = get_inst_names(value)
        results.append(tmp)

    return results


def _sync_host_with_db(hosts_info, business=None):
    results = {'added': [], 'deleted': [], 'updated': []}
    file_hosts = [Host(**host_info) for host_info in hosts_info]
    db_hosts = get_hosts_list(business=business)

    file_host_names = [host['name'] for host in hosts_info]
    db_host_names = [host.name for host in db_hosts]
    file_hosts_map = dict(zip(file_host_names, file_hosts))
    db_hosts_map = dict(zip(db_host_names, db_hosts))

    common_host_names = list(set(file_host_names).intersection(set(db_host_names)))
    added_host_names = list(set(file_host_names).difference(set(common_host_names)))
    deleted_host_names = list(set(db_host_names).difference(set(common_host_names)))

    app.logger.debug('db hosts map  ====> {}'.format(db_hosts_map))
    app.logger.debug('file hosts map  ====> {}'.format(file_hosts_map))
    # delete host
    for (host_name, host) in db_hosts_map.items():
        if host_name in deleted_host_names:
            host.delete()
            results['deleted'].append(host)

    # update host
    for (host_name, host) in file_hosts_map.items():
        if host_name in db_host_names:   # update the db host
            updated_info = {
                'updated_at': datetime.datetime.now(),
                'identity_ip': host.identity_ip,
                'os': host.os,
                'business': host.business,
                'others': host.others
            }
            updated_host = db_hosts_map[host_name].update(**updated_info)
            results['updated'].append(updated_host)

    # add host
    for (host_name, host) in file_hosts_map.items():
        if host_name in added_host_names:
            host.save()
            results['added'].append(host)

    app.logger.info('sync hosts with db  ====> {}'.format(results))

    return results


def _prepare_host_info(hosts_info, business, login_name):
    """
    Convert the raw hosts information
    Args:
        hosts_info: the raw host information from file/API
        business: the name of BUSINESS GROUP, LDDS, CLOUD
    Returns:
        the parsed hosts information
    """
    app.logger.info('Raw host information ====> {}'.format(hosts_info))

    key_map = BUSINESS_HOST_KEY_MAP.get(business, None)
    key_name_map = BUSINESS_HOST_KEYNAME_MAP.get(business, None)

    # app.logger.info('======> host key :{}, host key name: {}'.format(key_map, key_name_map))

    if not key_map or not key_name_map:
        return []

    results = []
    for host in hosts_info:
        host_info = {}
        others = []
        for key, value in host.items():
            if key in key_map:
                host_info[key_map[key]] = value
            else:
                others.append({
                    'key_cn': key_name_map[key],
                    'key_en': key,
                    'value': value
                })

        host_info.update({
            'business': business,
            'type': 'host',
            'modified_by': login_name,
            'others': json.dumps(others)   # convert to json string

        })

        results.append(host_info)

    app.logger.info('Converted host information ====> {}'.format(results))

    return results


########################################
#
# SYNC HOSTS with Scheduler related APIs
#
########################################
def sync_hosts_with_scheduler(sync_hosts):
    """
    Sync hosts with scheduler module
    Args:
        sync_hosts: the synced host from aops db, {'added': [..], 'deleted': [...], 'updated':[...]}
    Returns:
         the results fo sync hosts
    """

    results = {'added': [], 'deleted': [], 'updated': []}
    results['added'].extend(_prepare_inventory_hosts(sync_hosts.get('added')))
    results['deleted'].extend(_prepare_inventory_hosts(sync_hosts.get('deleted')))
    results['updated'].extend(_prepare_inventory_hosts(sync_hosts.get('updated')))

    app.logger.info('Post inventory hosts to scheduler, args: {}'.format(results))

    if not results['added'] and not results['deleted'] and not results['updated']:
        app.logger.info('NO sync inventory host with scheduler...')
        return None

    headers = {'Content-Type': 'application/json;charset=utf-8'}
    response = SchedulerApi('/v1/inventories/sync-hosts/').post(data=json.dumps(results), headers=headers)
    app.logger.info('Post inventory hosts to scheduler, result: {}'.format(response))

    return response


def _prepare_inventory_hosts(aops_hosts):
    """ generate inventory host info from apos host"""
    if not aops_hosts:
        return []

    app.logger.debug('Prepare inventory hosts, args: {}'.format(aops_hosts))

    key_map = {
        'name': 'name',
        'business': 'business',
        'identity_ip': 'ip',
        'os': 'os'

    }
    inventory_hosts = []
    for host in aops_hosts:

        inventory_host = {}
        for key1, key2 in key_map.items():
            inventory_host[key2] = host.__getattribute__(key1)

        inventory_host['accounts'] = [{'username': account.username, 'password': account.password}
                                      for account in host.accounts] if host.accounts else []

        inventory_host['params'] = [{'name': param.name, 'value': param.value}
                                    for param in host.params] if host.params else []
        inventory_host.update({'port': '2222'})   # hard code

        inventory_hosts.append(inventory_host)

    app.logger.debug('Prepare inventory hosts, result: {}'.format(inventory_hosts))

    return inventory_hosts


def _to_dict(host_obj):
    host = host_obj.to_dict()
    host['accounts'] = [{'username': account.username, 'password': account.password}
                        for account in host['accounts']] if host.get('accounts') else []

    host['params'] = [{'name': param.name, 'value': param.value}
                      for param in host['params']] if host.get('params') else []

    return host


def sync_hosts_with_cmdb_by_interval():
    """ sync hosts with cmdb by interval  polling"""
    pass


def sync_hosts_with_scheduler_by_message():
    pass

#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 2018/7/19 15:35
# @Author  : szf

from flask import current_app as app
import datetime
from sqlalchemy.orm.exc import NoResultFound
from aops.applications.exceptions.exception import ResourceNotFoundError, ResourceAlreadyExistError, Error
from aops.applications.database.apis.repository.repository import Repostiory
from aops.applications.database.apis.resource.host.group import init_business_groups, delete_business_groups

from aops.applications.database.models import SysConfigBusiness


# Business config APIs
def get_business_configs():
    return SysConfigBusiness.query.filter_by(is_deleted=False).all()


def get_business_config(identifier):
    try:
        business_config = SysConfigBusiness.query.filter_by(id=identifier, is_deleted=False).one()
    except NoResultFound:
        raise ResourceNotFoundError('BusinessConfig')
    return business_config


def create_business_configs(items):
    """ added/deleted/updated businesses"""
    business_configs = []
    results = sync_business_cfg_with_db(items)
    business_configs.extend(results['added'])
    business_configs.extend(results['updated'])
    _init_gitlab(results['added'])
    _init_default_business_group(results['added'])
    _delete_default_business_groups(results['deleted'])

    return business_configs


def _init_gitlab(businesses):
    for business in businesses:
        try:
            Repostiory().gitlab_init(business.name)
        except Error as e:
            app.logger.error('Initial git lab ERROR {}'.format(e.message))


def _init_default_business_group(businesses):
    if businesses:
        # delete default groups for Aops
        try:
            initial_groups = init_business_groups(businesses)
            app.logger.info('Inital default group for AOPS =======> {}'.format(initial_groups))
        except Error as e:
            app.logger.Error('[Error] Inital default group for AOPS =======> {}'.format(e.message))


def _delete_default_business_groups(businesses):
    if businesses:
        try:
            deleted_groups = delete_business_groups(businesses)
            app.logger.info('Delete default business group for AOPS =======> {}'.format(deleted_groups))
        except Error as e:
            app.logger.Error('[Error] Delete default group for AOPS =======> {}'.format(e.message))


def sync_business_cfg_with_db(items):
    results = {'added': [], 'deleted': [], 'updated': []}

    db_businesses = SysConfigBusiness.query.filter_by(is_deleted=False).all()
    post_businesses = [SysConfigBusiness(**item) for item in items]
    db_business_names = [business.name for business in db_businesses]
    post_business_names = [item.name for item in post_businesses]

    db_business_map = dict(zip(db_business_names, db_businesses))
    post_business_map = dict(zip(post_business_names, post_businesses))

    common_business_names = list(set(post_business_names).intersection(set(db_business_names)))
    added_business_names = list(set(post_business_names).difference(set(common_business_names)))
    deleted_business_names = list(set(db_business_names).difference(set(common_business_names)))

    # deleted business
    for (name, business) in db_business_map.items():
        if name in deleted_business_names:
            business.delete()
            results['deleted'].append(business)

            # delete a default business group

    # added business
    for (name, business) in post_business_map.items():
        if name in added_business_names:
            business.save()
            results['added'].append(business)

    # updated business
    for (name, business) in post_business_map.items():
        if name in common_business_names:
            data = {
                'updated_at': datetime.datetime.now(),
                'name': business.name,
                'description': business.description
            }
            updated_business = db_business_map[name].update(**data)
            results['updated'].append(updated_business)

    app.logger.debug('Sync business group ====>{}'.format(results))

    return results

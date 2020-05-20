#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 2018/7/19 15:34
# @Author  : szf
"""
Application Api
"""
import json
from flask import current_app, request, session
import datetime
from sqlalchemy.orm.exc import NoResultFound
from aops.applications.exceptions.exception import ResourceNotFoundError, ResourcesNotFoundError, \
    ResourceAlreadyExistError, NotFoundError, Error, ResourceNotUpdatedError

from aops.applications.database.models import Application, AppParameter
from aops.applications.common.cmdb_request import CmdbRequest
from aops.applications.database.apis.resource.host import host as host_apis
from aops.applications.database.apis.resource.application import parameter as app_param_apis

from aops.applications.lib import cmdb_api as cmdb

OFFLINE = 4
ONLINE = 3
NEW = 1
MODIFIED = 2


def get_application_list(page, per_page, name=None, type=None,
                         version=None, creator=None,publisher=None,
                         instance_name=None, instance_status=None,
                         start_time=None, end_time=None, fuzzy_query=None):
    """
    Get application list by filter
    """
    applications = Application.query.filter_by(is_deleted=False). \
        order_by(Application.created_at.desc())

    # Precise query
    if name:
        applications = applications.filter(Application.name.like("%{}%".format(name)))

    if type:
        applications = applications.filter(Application.type.like("%{}%".format(type)))

    if version:
        applications = applications.filter(Application.version.like("%{}%".format(version)))

    if creator:
        applications = applications.filter(Application.creator.like("%{}%".format(creator)))

    if publisher:
        applications = applications.filter(Application.publisher.like("%{}%".format(publisher)))

    if instance_name:
        applications = applications.filter(Application.instance_name.like("%{}%".format(instance_name)))

    if instance_status:
        applications = applications.filter(Application.instance_status.like("%{}%".format(instance_status)))

    if start_time and end_time:
        applications = applications.filter(Application.publish_time.between(start_time, end_time))

    # return pagination body
    try:
        applications = applications.paginate(page=page, per_page=per_page)
    except Exception as e:
        raise ResourceNotFoundError('Application', e.message)

    for application in applications.items:
        application.host_ips = application.host_ips.split(',') if application.host_ips else None
        application.type = _convert_app_type(application.type)

    return applications


def _convert_app_type(app_type):
    app_types = current_app.config['APP_TYPES'] if current_app.config['APP_TYPES'] else []
    type_map = {}
    for type in app_types:
        type_map[str(type['id'])] = type['label']

    return type_map[app_type]


def get_application_with_id(identifier):
    try:
        application = Application.query.filter_by(id=identifier, is_deleted=False).one()
        if application.host_ips:
            application.host_ips = application.host_ips.split(',')
        application.type = _convert_app_type(application.type)
    except NoResultFound:
        raise ResourcesNotFoundError('Application')
    return application


def create_application(args):
    """ create an application """
    business = request.cookies.get('BussinessGroup')
    login_name = session.get('user_info').get('user')
    app_instance = Application.query.filter_by(name=args.instance_name).first()
    if app_instance and not app_instance.is_deleted:
        raise ResourceAlreadyExistError('Application')
    if app_instance and app_instance.is_deleted:
        app_instance.instant_name = args.instant_name + '_is_deleted_' + str(app_instance.id)

    data = {
        'instance_name': args.instance_name,
        'instance_status': 1,
        'instance_description': args.instance_description,
        'name': args.name,
        'version': args.version,
        'language': args.language,
        'type': args.type,
        'creator': login_name,
        'business_group': business,
        'sw_package_repository': args.sw_package_repository,
        'cfg_file_repository': args.cfg_file_repository
    }

    if args.parameters:
        args.parameters = [AppParameter(**param) for param in args.parameters]
        data.update({'parameters': args.parameters})

    application = Application.create(**data)

    application.type = _convert_app_type(application.type)

    # create an app instance into CMDB
    app_id_cmdb = create_app_instance_into_cmdb(application)
    application.update(inst_id_cmdb=app_id_cmdb)
    current_app.logger.info('Create an app into CMDB, name: {}, id: {}'.format(application.instance_name, app_id_cmdb))

    return application


def update_application_with_id(identifier, args):
    """ update application info"""
    try:
        application = Application.query.filter_by(id=identifier, is_deleted=False).first()
    except NotFoundError as e:
        raise ResourcesNotFoundError('Application')
    # login_name = session.get('user_info').get('user')
    login_name = "zhangsan"
    if application.instance_status != NEW or application.instance_status != MODIFIED:
        raise ResourceNotUpdatedError('Application')
    data = {
        'instance_name': args.instance_name,
        'instance_status': 2,
        'instance_description': args.instance_description,
        'name': args.name,
        'version': args.version,
        'language': args.language,
        'type': args.type,
        'creator': login_name,
        'sw_package_repository': args.sw_package_repository,
        'cfg_file_repository': args.cfg_file_repository
    }
    if args.parameters:
        args.parameters = [AppParameter(**param) for param in args.parameters]
        data.update({'parameters': args.parameters})
    data.update(updated_at=datetime.datetime.now())
    updated_app = application.update(**data)

    updated_app.type = _convert_app_type(updated_app.type)

    # update an app instance into CMDB
    result = cmdb.update_app_instance(updated_app.inst_id_cmdb, updated_app)
    current_app.logger.info('Update an app into CMDB, name: {}, result: {}'.format(updated_app.instance_name, result))

    return updated_app


def update_online_with_id(identifier, data):
    """
    updated the application publish info with identifier by job execution
    when a job publishing a application is executing.
    Args:
        identifier：application instance ID
        data: including publisher, publish_time, instance_status(3: published),
            execution_id: it is used to fetch host_ips from host_results table in Scheduler module
    Returns:
        the updated application
    """
    app_instance = Application.query.filter_by(id=identifier, is_deleted=False).first()
    login_name = session.get('user_info').get('user')
    updated_data = {
        'publisher': login_name,
        'publish_time': datetime.datetime.now(),
        'instance_status': ONLINE,
        'host_ips': ''
    }
    updated_instance = app_instance.update(**updated_data)
    sync_app_status_with_cmdb(updated_instance.id, updated_instance.inst_id_cmdb, ONLINE)
    return updated_instance


def update_offline_with_id(identifier, data):
    """
    updated the application offline info with identifier
    when a app-offline job is executing.
    Args:
        identifier：application instance ID
        data: including publisher, publish_time, instant_status(3), execution_id
            execution_id: it is used to fetch host_ips from host_results table in Scheduler module
    Returns:
        the updated application except host_ips
    Exceptions:
        some host are not offline
    """
    app_instance = Application.query.filter_by(id=identifier, is_deleted=False).first()
    updated_data = {
        'instance_status': OFFLINE,  # offline
        'host_ips': ''
    }
    updated_instance = app_instance.update(**updated_data)
    sync_app_status_with_cmdb(updated_instance.id, updated_instance.inst_id_cmdb, OFFLINE)
    return updated_instance


def delete_application_with_id(app_id):
    """ deleted a application: status is offline (host ips are None)"""
    try:
        application = Application.query.filter_by(id=app_id, is_deleted=False).one()
    except NoResultFound as e:
        raise ResourcesNotFoundError('Application')

    if application.instance_status == OFFLINE and application.host_ips is None:

        cmdb_result = delete_app_instance_from_cmdb(app_id)
        current_app.logger.info("delete_app_instance_from_cmdb=====>{}".format(cmdb_result))
        return application.update(is_deleted=False, deleted_at=datetime.datetime.now())
    else:
        raise Error("application {} is not 'OFFLINE', didn\'t allow delete".format(application.id), 403)


def delete_applications_with_ids(app_ids):
    return [delete_application_with_id(app_id) for app_id in app_ids]


def get_applications_list():
    applications = Application.query.filter_by(is_deleted=False).order_by(Application.created_at.desc())
    return applications.all()


def get_application_list_search(instance_name=None, name=None, type=None,
                                version=None, instance_status=None, creator=None, publisher=None):
    """
    Get an filter list

    Args:
        field_name: the field name for filter, eg,name, type, status, version,
         creator, publisher, instance_name

        field_value: the field value

    Return:
         the filter  list
    """
    applications = Application.query.filter_by(is_deleted=False). \
        order_by(Application.created_at.desc())

    # Precise query
    if name:
        applications = applications.filter(Application.name.like("%{}%".format(name)))

    if type:
        applications = applications.filter(Application.type.like("%{}%".format(type)))

    if version:
        applications = applications.filter(Application.version.like("%{}%".format(version)))

    if creator:
        applications = applications.filter(Application.creator.like("%{}%".format(creator)))

    if publisher:
        applications = applications.filter(Application.publisher.like("%{}%".format(publisher)))

    if instance_name:
        applications = applications.filter(Application.instance_name.like("%{}%".format(instance_name)))

    if instance_status:
        applications = applications.filter(Application.instance_status.like("%{}%".format(instance_status)))

    applications = applications.all()
    for application in applications:
        application.host_ips = application.host_ips.split(',') if application.host_ips else None
        application.type = _convert_app_type(application.type)

    return applications


###########################################
#
#  Application API related CMDB
#
###########################################
def create_app_instance_into_cmdb(app_instance):
    """ do action when a app instance is added into AOPS
    Args:
        app_instance: a object Application in aops
    """
    # app_instance = get_application_with_id(aops_app_id)
    cmdb_app_id = cmdb.create_app_if_not_exist(app_instance)
    return cmdb_app_id


def delete_app_instance_from_cmdb(aops_app_id):
    """ do action when a app instance is removed from AOPS"""
    app_instance = get_application_with_id(aops_app_id)
    return cmdb.delete_app_if_exist(app_instance.instance_name)


def sync_app_status_with_cmdb(app_id_aops, app_id_cmdb, status):
    """
    sync the application instance into CMDB
    Args:
        app_id_aops: The ID of application instance in Aops
        app_id_cmdb: The name of application instance in CMDB
        status: The status of application instance , offine/online
    Returns:
        The synced application instance
    """
    current_app.logger.info('SYNC APP status with CMDB args: app_ids_cmdb<{}>, app_id_cmdb<{}>, status<{}>'.
                            format(app_id_aops, app_id_cmdb, status))
    # get application with identifier
    app_instance = get_application_with_id(app_id_aops)
    host_names = [{'name': host.name, 'business': host.business} for host in app_instance.hosts]

    for item in host_names:
        host_name = item['name']
        business = item['business']
        host_instance_cmdbs, count = cmdb.get_host_with_name(host_name, business)
        host_instance_cmdb = host_instance_cmdbs[0]
        host_instance_id = host_instance_cmdb['bk_inst_id']
        app_ids_cmdb = [app['bk_inst_id'] for app in host_instance_cmdb['app']]

        if status == ONLINE:     # 建立关联
            app_ids_cmdb.append(app_id_cmdb)
            app_ids_cmdb = list(set(app_ids_cmdb))
            current_app.logger.info('Application Online, app_ids_cmdb:{}, instance_id:{}'.format(app_ids_cmdb, host_instance_id))
            result = cmdb.update_app_into_host(_to_str(app_ids_cmdb), host_instance_id, business)

        elif status == OFFLINE:  # 取消关联
            if app_id_cmdb in app_ids_cmdb:
                app_ids_cmdb.remove(app_id_cmdb)
            app_ids_cmdb = list(set(app_ids_cmdb))
            current_app.logger.info('Application Offine, app_ids_cmdb:{}'.format(app_ids_cmdb, host_instance_id))
            result = cmdb.update_app_into_host(_to_str(app_ids_cmdb), host_instance_id, business)

    return result


def _to_str(int_list):
    str_list = [str(item) for item in int_list]
    return ','.join(str_list)
#!/usr/bin/env python
# -*- coding:utf-8 -*-
from ..user_permission.role import create_default_role, get_role_with_name
from ..user_permission.permission import get_permission_list
from ..system.user.user import create_default_user, get_user_with_name, get_business_with_name
from aops.applications.exceptions.exception import ResourceNotFoundError

def add_default_permissions_for_role(**kwargs):
    """
    Add default permissions to the role
    Args:
        role_id: role id
        args: dict which contain permission ids

    Returns:
        All newly added permissions
    """
    name = kwargs.get('name')
    permissions = kwargs.get('permissions')
    role = get_role_with_name(name=name)
    if '*' in permissions:
        permissions = get_permission_list()
    else:
        permissions = None
    if permissions is not None:
        [role.permissions.append(permission) for permission in permissions if permission not in role.permissions.all()]
    return role.save()


def generate_default_role():
    """
    generate_default role
    Args:


    Returns:
        the created role
    """
    data = [
        {'name': 'admin', 'description': u'超级管理员'},
        {'name': 'operation_admin', 'description': u'业务运维管理员'},
        {'name': 'operator', 'description': u'业务运维人员'},
        {'name': 'auditor', 'description': u'审计人员'},
    ]
    # generate roles
    [create_default_role(**role) for role in data]

    permissions = [
        {'name': 'admin', 'permissions': ['*']},
        {'name': 'operation_admin', 'permissions': []},
        {'name': 'operator', 'permissions': []},
        {'name': 'auditor', 'permissions': []}
    ]

    # permissions
    return [add_default_permissions_for_role(**role) for role in permissions]


def generate_default_user():
    """
    generate_default role
    Args:


    Returns:
        the created role
    """
    data = {
        'username': 'admin',
        'password': 'admin',
        'realname': 'admin',
        # 'business': 'LDDS',
        'email': 'zfsun@sse.com.cn',
        'telephone': '18101729630',
        'status': 1,
        'init_login': 0,
        'modified_by': 'system_god',
        'token': 'MqGru9eByzSeo96PZA',
    }

    # generate user
    user = create_default_user(**data)
    if user is None:
        user = get_user_with_name('admin')
    try:
        role = get_role_with_name('admin')
        if role not in user.roles.all():
            user.roles.append(role)
        business = get_business_with_name('LDDS')
        if business not in user.businesses.all():
            user.businesses.append(business)
        user.save()
<<<<<<< HEAD
    except Exception as e:
        pass
=======
    except ResourceNotFoundError as e:
        print e.msg
>>>>>>> use flask migrate to manage db

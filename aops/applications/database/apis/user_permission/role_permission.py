#!/usr/bin/env python
# -*- coding:utf-8 -*-

from aops.applications.database import db
from aops.applications.database.apis.user_permission.permission import get_permission_with_id
from aops.applications.database.apis.user_permission.role import get_role_with_id
from aops.applications.exceptions.exception import ResourceNotFoundError
from aops.applications.exceptions.exception import ValidationError


def get_role_permissions(identifier, page=1, per_page=10):

    role = get_role_with_id(identifier)
    permissions = role.permissions
    try:
        return permissions.paginate(page=page, per_page=per_page)
    except Exception as e:
        raise ResourceNotFoundError('Permission', e.message)


def _add_role_permission(role, permission_id, new_role_permission_list):
    permission = get_permission_with_id(permission_id)
    role.permissions.append(permission)
    db.session.add(role)
    new_role_permission_list.append(permission)


def add_role_permissions(role_id, args):
    """
    Add a permission to the role
    Args:
        role_id: role id
        args: dict which contain permission ids

    Returns:
        All newly added permissions
    """
    try:
        role = get_role_with_id(role_id)
        new_role_permission_list = []
        # permission_id_list = args.permission_ids.split(',')
        for permission_id in args.permission_ids:
            _add_role_permission(role, permission_id, new_role_permission_list)
        db.session.commit()
        return new_role_permission_list
    except Exception as e:
        raise ValidationError(e.message)


def _delete_role_permission(role, permission_id, deleted_permissions_list):
    permission = get_permission_with_id(permission_id)
    role.permissions.remove(permission)
    deleted_permissions_list.append(permission)


def delete_role_permissions(role_id, args):
    """
    Delete a permission to the role
    Args:
        role_id: role id
        args: dict which contain permission ids

    Returns:
        All newly deleted permissions
    """
    try:
        role = get_role_with_id(role_id)
        deleted_permissions_list = []
        permission_id_list = args.permission_ids
        for permission_id in permission_id_list:
            _delete_role_permission(role, permission_id, deleted_permissions_list)
        db.session.commit()
        return deleted_permissions_list
    except Exception as e:
        raise ValidationError(e.message)

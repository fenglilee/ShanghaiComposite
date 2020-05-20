#!/usr/bin/env python
# -*- coding:utf-8 -*-

from aops.applications.database import db
from aops.applications.database.apis import user as user_api
from aops.applications.database.apis.user_permission.role import get_role_with_id


def get_user_roles(args):
    """
    Get all the user's roles
    Args:
        args:dict which contain user id

    Returns:
        The user's all roles
    """
    user = user_api.get_user_with_id(args)
    user_roles = user.roles.all()
    return user_roles


def _add_user_role(user, role_id, new_user_role_list):
    role = get_role_with_id(role_id)
    user.roles.append(role)
    db.session.add(user)
    new_user_role_list.append(role)


def add_user_roles(user_id, args):
    """
    Add a role to the user
    Args:
        user_id: user id
        args: dict which contain role ids

    Returns:
        All newly added roles
    """
    user = user_api.get_user_with_id(user_id)
    new_user_role_list = []
    # role_id_list = args.role_ids.split(',')
    for role_id in args.role_ids:
        _add_user_role(user, role_id, new_user_role_list)
    db.session.commit()
    return new_user_role_list


def _delete_user_role(user, role_id, deleted_user_role_list):
    role = get_role_with_id(role_id)
    user.roles.remove(role)
    deleted_user_role_list.append(role)


def delete_user_roles(user_id, args):
    """
    Delete a role to the user
    Args:
        user_id: user id
        args: dict which contain role ids

    Returns:
        All newly deleted roles
    """
    user = user_api.get_user_with_id(user_id)
    deleted_user_role_list = []
    # role_id_list = args.role_ids.split(',')
    for role_id in args.role_ids:
        _delete_user_role(user, role_id, deleted_user_role_list)
    db.session.commit()
    return deleted_user_role_list



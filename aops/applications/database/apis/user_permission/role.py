#!/usr/bin/env python
# -*- coding:utf-8 -*-

from flask import session
from datetime import datetime
from sqlalchemy import desc
from sqlalchemy.orm.exc import NoResultFound
from aops.applications.database.models import Role
from aops.applications.exceptions.exception import ResourceNotFoundError
from aops.applications.exceptions.exception import ValidationError


def get_roles_list(page=1, per_page=10):
    """
    Get all roles
    Returns:
        role list
    """
    roles = Role.query.filter_by(is_deleted=False).order_by(desc(Role.updated_at))
    try:
        return roles.paginate(page=page, per_page=per_page)
    except Exception as e:
        raise ResourceNotFoundError('Role', e.message)


def list_roles():
    roles = Role.query.filter_by(is_deleted=False).order_by(desc(Role.updated_at))
    return roles.all()


def create_role(args):
    """
    create a role with args
    Args:
        args: dict which contain role_name

    Returns:
        the created role
    """
    user = session.get('user_info').get('user')
    role = Role.create(name=args.name, description=args.description, created_user=user)
    return role.to_dict()


def create_default_role(**kwargs):
    """
    create role used by system init
    Args:
        args: dict which contain role_name

    Returns:
        the created role
    """
    name = kwargs.get('name')
    role = Role.query.filter_by(name=name).first()
    if role:
        if role.is_deleted:
            return 403
        else:
            kwargs.update(updated_at=datetime.now())
            return role.update(**kwargs)
    return Role.create(**kwargs)


def get_role_with_id(identifier):
    """
    Get a role with identifier
    Args:
        identifier: ID for role item

    Returns:
        Just the role item with this ID.

    Raises:
          NotFoundError: role is not found
    """
    try:
        role = Role.query.filter_by(id=identifier, is_deleted=False).one()
    except NoResultFound:
        raise ResourceNotFoundError('Role', identifier)
    return role


def get_role_with_name(name):
    """
    Get a role with identifier
    Args:
        name: name for role item

    Returns:
        Just the role item with this name.

    Raises:
          NotFoundError: role is not found
    """
    try:
        role = Role.query.filter_by(name=name, is_deleted=False).one()
    except NoResultFound:
        raise ResourceNotFoundError('Role', name)
    return role


def delete_role_with_id(identifier):
    """
    Delete a role with identifier
    Args:
        identifier: ID for role item

    Returns:
        Just the role item with this ID.
    """
    role = get_role_with_id(identifier)
    user = role.users.all()
    if user:
        raise ValidationError('present role has been used')
    try:
        role = role.update(is_deleted=True)
        return role
    except Exception as e:
        raise ValidationError(e.message)


def update_role_with_id(identifier, role_info):
    """
    Update a role with identifier
    Args:
        identifier: ID for role item
        role_info: update role with this info

    Returns:
        Just the role item with this ID.
    """
    role_info.update(updated_at=datetime.now())
    role = get_role_with_id(identifier)
    return role.update(**role_info)


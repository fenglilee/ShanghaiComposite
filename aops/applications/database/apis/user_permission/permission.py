#!/usr/bin/env python
# -*- coding:utf-8 -*-
from sqlalchemy.orm.exc import NoResultFound

from aops.applications.database.models import Permission
from aops.applications.exceptions.exception import ResourceNotFoundError
from datetime import datetime


def get_permission_list():
    """
    Get all permission items
    Returns:
        Permission items list
    """
    return Permission.query.filter_by(is_deleted=False).all()


def create_permission(**kwargs):
    permission = kwargs.get('permission')
    permission = Permission.query.filter_by(permission=permission).first()
    if permission:
        if permission.is_deleted:
            return 'already exists', 403
        else:
            kwargs.update(updated_at=datetime.now())
            return permission.update(**kwargs)
    return Permission.create(**kwargs)


def get_permission_with_id(identifier):
    """
    Get a permission with identifier
    Args:
        identifier: ID for permission item

    Returns:
        Just the permission item with this ID.

    Raises:
          NotFoundError: permission is not found
    """
    try:
        permission = Permission.query.filter_by(id=identifier, is_deleted=False).one()
    except NoResultFound:
        raise ResourceNotFoundError('Permission', identifier)
    return permission

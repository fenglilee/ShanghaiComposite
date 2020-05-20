#!/usr/bin/env python
# -*- coding:utf-8 -*-
from flask import current_app as app
from aops.applications.database.models.system.user import Permission
from aops.applications.exceptions.exception import ResourcesNotFoundError
from aops.applications.database.apis.user_permission.role import get_role_with_id


def get_permission_list(role_id=None):
    """s
    Get all file review items
    Returns:
        file review items list
    """
    try:
        role = get_role_with_id(identifier=role_id)
        role_permissions = role.permissions.all()
        all_permissions = Permission.query.filter_by(is_deleted=False).order_by(Permission.updated_at.desc()).all()
        add_permissions = [permission for permission in all_permissions if permission not in role_permissions]
        return add_permissions
    except Exception as e:
        raise ResourcesNotFoundError(e.message)


def get_permission_pagination_list(page, per_page, fq=None):
    """
    Get items
    Returns:
        file review items list
    """
    q = Permission.query.filter_by(is_deleted=False).order_by(Permission.updated_at.desc())
    if fq:
        q = q.filter(Permission.permission.concat(Permission.description).like("%{}%".format(fq)))
    try:
        return q.paginate(page=page, per_page=per_page)
    except Exception as e:
        app.logger.error("Permissions list failed: " + str(e))
        raise ResourcesNotFoundError("Permissions")

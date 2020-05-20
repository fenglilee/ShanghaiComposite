#!/usr/bin/env python
# -*- coding:utf-8 -*-
from flask import session, request, abort, current_app as app
from aops.applications.database.apis.system.user.user import get_user_with_name
from aops.applications.database.apis.user_permission.user_role import get_user_roles
from aops.applications.database.apis.user_permission.role_permission import get_role_permissions


def _update_user_permissions(username):
    user = get_user_with_name(username)
    privileges = [(role.name, permission.permission) for role in user.roles for permission in
                  role.permissions]
    roles = list(set(map(lambda item: item[0], privileges)))
    permissions = list(set(map(lambda item: item[1], privileges)))
    session['user_info'] = {
        'user': user.username,
        'roles': roles,
        'permissions': permissions
    }
    app.logger.debug('User info in Session: {}'.format(session['user_info']))


def _in_white_list(base_url):
    white_list = ['login', 'logout', 'swagger']
    for item in white_list:
        if item in base_url:
            return True
    return False


@app.before_request
def check_user():
    """
    check the login status
    """

    if not _in_white_list(request.base_url):
        if 'user_info' not in session:
            app.logger.error("User info hasn't be found")
            abort(401, 'No user logged in :( , redirect to login!')
        else:
            app.logger.info('User have logged in :)')
            user_info = session.get('user_info', None)
            if user_info:
                username = user_info.get('user', None)
                if username:
                    _update_user_permissions(username)
                else:
                    abort(401, u'未获取到用户session信息，请联系管理员')
            else:
                abort(401, u'登录失效')
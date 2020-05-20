#!/usr/bin/env python
# -*- coding:utf-8 -*-

from flask_restplus import Api

from functools import wraps
from flask import request, session, abort
from flask import current_app as app
import json
from aops.applications.database.apis.audit.audit import add_audit_item

api = Api(
    title='aops',
    version='1.0',
    description='AOPS\' api document',
    doc='/api/swagger-doc'
)


def _generate_permission_list(func_name, action=None):
    """
    Args:
        func_name:
        action:

    Returns:

    """
    """
    :param action: url's specific action
    :return: current permission list
    """

    r_endpoint = request.endpoint
    url_rule = request.url_rule

    # based on namespaces/resources/function_name generate permission_name.
    for namespace in api.namespaces:
        cur_permission_list = [namespace.name.split('/')[-1] + "_" + func_name + "_" + res[0].__name__ for res in
                               namespace.resources if namespace.resources and r_endpoint == res[0].endpoint]
        if len(cur_permission_list) == 1:
            break
        else:
            continue
    if len(cur_permission_list) == 1:
        permission = cur_permission_list[0]
    else:
        abort(400, u'基于{}未能生成对应的权限'.format(r_endpoint))

    # permission append action key.
    if isinstance(action, list):
        cur_action = [i for i in url_rule.split('/') if i in action]
        permission_action_list = [permission + "_" + a.lower() for a in cur_action]
        cur_permission_list = permission_action_list
    elif action:
        abort(400, u'action 定义必须为列表')
    else:
        pass
    app.logger.info("endpoint: {}, permission value: {}".format(r_endpoint, cur_permission_list))
    return cur_permission_list


def _auth_audit_log(result, cur_list, username, source_ip, r_id, msg):
    """

    Args:
        result: function result
        cur_list: current permission list
        username: session user's info
        source_ip: user's source ip address
        r_id: resource_id
        msg: custom's message

    Returns: null

    """
    if isinstance(result, tuple):
        operation_status = result[1]
    else:
        operation_status = 200
    cur_list_split = cur_list[0].split('_')
    resource = cur_list_split[0]
    operation = '_'.join(cur_list_split[1:])
    app.logger.debug(','.join(cur_list))
    audit_item = {
        'user': username,
        'source_ip': source_ip,
        'resource': resource,
        'resource_id': r_id,
        'operation': operation,
        'status': operation_status,
        'message': msg}
    response = add_audit_item(**audit_item)
    if response:
        app.logger.info("add audit success: {}".format(response))
    else:
        app.logger.info("add audit failed: {}".format(response))


def passport_auth(action=None, notes=None):
    """
    Args:
        action: list type,  eg: action=['stop-task', 'update-task']
        notes: audit log {'type': 'task', 'args': {'identifier': 2}, 'info': ''}
    Returns:

    """
    def passport_decorate(f):
        """
        Check user permissions & audit
        session['user_info']={'permissions':[], 'user': 'aops-user01', etc..}
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # passport_auth switch
            enable_auth = app.config.get('PASSPORT_AUTH', True)
            if not enable_auth:
                return f(*args, **kwargs)
            user_info = session.get('user_info', None)
            if user_info is None:
                abort(401, u'登录失效')
            # user_info = session.get('user_info', {'permissions':
            # ['todos_getTodos', 'todos_getTodo'], 'user': 'aops-user01'})

            cur_permission_list = _generate_permission_list(f.__name__, action=action)

            if isinstance(user_info, dict):
                user_permissions_list = user_info.get('permissions', None)
            else:
                abort(400, u'未获取当前用户的权限定义')

            user_permissions_list = [] if user_permissions_list is None else user_permissions_list
            app.logger.info("user_permissions_list: {}".format(user_permissions_list))

            app.logger.debug("===>current_permissions_list: {}".format(cur_permission_list))
            app.logger.debug("===>user_permissions_list: {}".format(user_permissions_list))
            if not set(cur_permission_list).issubset(set(user_permissions_list)):
                abort(403, u'权限拒绝')

            result = f(*args, **kwargs)

            username = user_info.get('user', None)
            resource_id = kwargs.get('identifier', None)
            message = {'path_args': kwargs, 'notes': notes}
            message = json.dumps(message)
            source_ip = request.remote_addr
            if not username:
                abort(400, u'未获取当前用户名')
            # audit switch
            enable_audit = app.config.get('PASSPORT_AUDIT', True)
            if enable_audit:
                _auth_audit_log(result=result, cur_list=cur_permission_list, username=username, source_ip=source_ip,
                                r_id=resource_id, msg=message)
            return result
        return decorated_function
    return passport_decorate


def only_audit_log(username=None, action=None, notes=None):
    """

    Args:
        username:
        action:
        notes:

    Returns:

    """
    if username is None:
        user_info = session.get('user_info', None)
        if user_info is None:
            abort(403, u'登录失效')
        username = user_info.get('user')

    def audit_decorate(f):
        """
        Args:
            audit detail
            session['user_info']={'permissions':[], 'user': 'aops-user01', etc..}
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # audit switch
            enable_audit = app.config.get('PASSPORT_AUDIT', True)
            result = f(*args, **kwargs)
            if enable_audit:
                resource_id = kwargs.get('identifier', None)
                source_ip = request.remote_addr

                cur_permission_list = _generate_permission_list(f.__name__, action=action)
                message = {'path_args': kwargs, 'notes': notes}
                message = json.dumps(message)

                _auth_audit_log(result=result, cur_list=cur_permission_list, username=username, r_id=resource_id,
                                msg=message, source_ip=source_ip)
            return result
        return decorated_function
    return audit_decorate


from aops.applications.handlers.v1.user_permission import ns as role_ns
from aops.applications.handlers.v1.todo import ns as todo_ns
from aops.applications.handlers.v1.task.task import ns as task_ns
from aops.applications.handlers.v1.job.instant_command import ns as instant_command_ns
from aops.applications.handlers.v1.job.job import ns as job_ns
from aops.applications.handlers.v1.ops_job.process import ns as process_ns
from aops.applications.handlers.v1.ops_job.timed_process import ns as timed_process_ns
from aops.applications.handlers.v1.ops_job.instant_process import ns as instant_process_ns
from aops.applications.handlers.v1.repository.repository import ns as repository_ns
from aops.applications.handlers.v1.system import sysconfig_ns, user_ns, auth_ns, message_ns
from aops.applications.handlers.v1.resource import app_ns, host_ns, group_ns
from aops.applications.handlers.v1.audit.audit import ns as audit_ns
from aops.applications.handlers.v1.bucket.file_bucket import ns as bucket_ns
from aops.applications.handlers.v1.worker.statistic import ns as worker_ns
from aops.applications.handlers.v1.job.daily_inspection import ns as daily_ns
from aops.applications.handlers.v1.approval.approval import ns as approval_ns
from aops.applications.handlers.v1.permission.permission import ns as permission_ns
from aops.applications.handlers.v1.resource.statistics.statistics import ns as statistics_ns

api.add_namespace(todo_ns, path='/v1/todos')
api.add_namespace(user_ns, path='/v1/users')
api.add_namespace(auth_ns, path='/v1/auth')
api.add_namespace(role_ns, path='/v1/roles')
api.add_namespace(task_ns, path='/v1/tasks')
api.add_namespace(job_ns, path='/v1/jobs')
api.add_namespace(process_ns, path='/v1/processes')
api.add_namespace(instant_process_ns, path='/v1/instant-processes')
api.add_namespace(timed_process_ns, path='/v1/timed-processes')
api.add_namespace(instant_command_ns, path='/v1/command')
api.add_namespace(host_ns, path='/v1/hosts')
api.add_namespace(group_ns, path='/v1/groups')
api.add_namespace(sysconfig_ns, path='/v1/sysconfigs')
api.add_namespace(message_ns, path='/v1/messages')
api.add_namespace(app_ns, path='/v1/applications')
api.add_namespace(repository_ns, path='/v1/repositories')
api.add_namespace(audit_ns, path='/v1/audit')
api.add_namespace(bucket_ns, path='/v1/buckets')
api.add_namespace(worker_ns, path='/v1/workers')
api.add_namespace(approval_ns, path='/v1/approvals')
api.add_namespace(daily_ns, path='/v1/daily')
api.add_namespace(permission_ns, path='/v1/permissions')
api.add_namespace(statistics_ns, path='/v1/statistics')


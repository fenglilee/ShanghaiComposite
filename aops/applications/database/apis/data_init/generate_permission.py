#!/usr/bin/env python
# -*- coding:utf-8 -*-
from aops.applications.database.apis.user_permission.permission import create_permission


def generate_permissions(api):
    """
    generate permissions based on Namespaces

    namespace_Method_resource
    eg: 'repository_get_projects'

    """
    namespaces = api.namespaces
    permission_data = []
    for namespace in namespaces:
        namespace_name = namespace.name.split('/')[-1]
        namespace_desc = namespace.description
        for res in namespace.resources:
            res_name = res[0].__name__
            permission_list = [{"resource": namespace_name, "operation": m.lower() + '_' + res_name,
                                "permission": namespace_name + '_' + m.lower() + '_' + res_name,
                                "description": namespace_desc} for m in res[0].methods]
            permission_data += permission_list

    # app.logger.debug(permission_data)
    [create_permission(**permission) for permission in permission_data]

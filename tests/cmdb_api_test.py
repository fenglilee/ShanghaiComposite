#!/usr/bin/env python
# -*- coding:utf-8 -*-

from flask import Flask
from aops.applications.lib.cmdb_api import get_all_machine_list,\
    get_host_list, get_host_with_name, get_app_instance_with_name,\
    update_app_into_host, delete_app_if_exist, create_app_instance, update_app_instance
from aops.applications.handlers.v1.utils import Dynamic

if __name__ == '__main__':
    app = Flask("cmdb_api_test")

    with app.app_context():
        # get_all_machine_list()
        # get_host_list('CLOUD')
        # get_host_with_name("EC-C1-RZF2-VM6", "CLOUD")
        # get_app_instance_with_name("test_fxr_aops")
        # update_app_into_host("67", "96", "CLOUD")
        updated_app_info = {

                "instance_name": "app_v16",
                "instance_status": 1,

                "version": "master",

                "type": 1,
                "sw_package_repository": "LDDS/applications",
                "cfg_file_repository": "LDDS/configurations"


        }
        d = Dynamic(updated_app_info)
        # delete_app_if_exist('test_for_aops2')
        print update_app_instance(631, d)
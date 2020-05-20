#!/usr/bin/env python
# -*- coding:utf-8 -*-

from gevent import monkey; monkey.patch_all()
from flask import Flask

from aops.applications.common.utils import get_app_mode
from aops.applications.handlers.v1 import api as apiv1
from aops.applications.database import db
from aops.applications.common.log import init_logger
from aops.applications import register_polling_tasks
from aops.conf.server_config import configs
from flask_migrate import Migrate


def create_app():
    app = Flask("aops")
    # load config from config file
    app.config.from_object(configs[get_app_mode()])

    init_logger(app)
    db.init_app(app)
    Migrate(app, db)
    # with app.app_context():
    #     db.create_all()
        # import aops.applications.pre_request
    apiv1.init_app(app)
    return app


def create_testing_app(extra_config):
    app = Flask("testing_aops")
    # load config from config file
    app.config.from_object(configs[get_app_mode("testing")])

    # load config from map for testing purpose
    app.config.from_mapping(extra_config)

    init_logger(app)
    db.init_app(app)
    # with app.app_context():
    #     db.create_all()
    apiv1.init_app(app)
    return app


if __name__ == '__main__':
    from aops import application
    with application.app_context():
        from aops.applications.database.apis.data_init.generate_permission import generate_permissions
        from aops.applications.database.apis.data_init.generate_roles import generate_default_role
        from aops.applications.database.apis.data_init.generate_roles import generate_default_user
        from aops.applications.database.apis.system.sysconfig import init_system_config
        generate_permissions(apiv1)
        generate_default_role()
        generate_default_user()
        init_system_config()

    register_polling_tasks(application)
    application.run(debug=application.config['DEBUG'], host='0.0.0.0', port=5000, use_reloader=False)

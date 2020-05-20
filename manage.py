# !/usr/bin/python
# -*- coding:utf-8 -*-

"""
@author: fengli
@time: 2018/8/24 下午4:52
@file: manage
"""

from aops.app import create_app
from aops.applications.database.database import db
from flask_script import Manager
from flask_migrate import Migrate
from flask_migrate import MigrateCommand
from aops.applications.database.models import *


app = create_app()
db.init_app(app)
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()

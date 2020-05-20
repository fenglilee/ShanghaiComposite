#!user/bin/env python
# -*- coding:utf-8 -*-
from flask_restplus import Namespace

ns = Namespace('/v1/roles', description='ROLES operations')

import role
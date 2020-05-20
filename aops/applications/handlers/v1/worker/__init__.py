#!/usr/bin/env python
# -*- coding:utf-8 -*-
from flask_restplus import Namespace

ns = Namespace('/v1/workers', description='Get all celery worker stats')

import health
import statistic

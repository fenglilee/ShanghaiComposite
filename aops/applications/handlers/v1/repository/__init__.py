#!/usr/bin/env python
# -*- coding:utf-8 -*-
from flask_restplus import Namespace

ns = Namespace('/v1/repositories', description='git repository operations')

import repository
import project
import review
import risk_command

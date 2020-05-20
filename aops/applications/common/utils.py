#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os


def get_app_mode(mode=None):
    if mode is not None:
        return mode
    return os.getenv("APP_MODE", "development")

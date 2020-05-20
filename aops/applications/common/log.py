#!/usr/bin/env python
# -*- coding:utf-8 -*-
import json
import logging
import logging.config
import os


def init_logger(app):
    root_path = app.config.root_path
    if os.path.basename(root_path) == "aops":
        config_path = os.path.join(root_path, "conf", "logger_config.json")
    else:
        config_path = os.path.join(root_path, "aops", "conf", "logger_config.json")
    with open(config_path, 'r') as f:
        text_config = f.read()

    logging.config.dictConfig(json.loads(text_config))

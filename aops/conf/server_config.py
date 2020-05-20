#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
from datetime import timedelta


class Config(object):
    # Flask Config
    DEBUG = False
    TESTING = False
    ENV = "development"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(os.path.join("applications", "database", "sqlite3.db"))
    BUNDLE_ERRORS = True
    SECRET_KEY = 'G42Q&vM+fF9b(jm/(bxt=6Rl'
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    SESSION_REFRESH_EACH_REQUEST = True
    ERROR_404_HELP = False
    SQLALCHEMY_ECHO = False
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024

    # AOPS config
    PASSPORT_AUTH = True
    PASSPORT_AUDIT = True

    UPLOAD_FOLDER = '/upload_script'
    UPLOADED_FILES_DENY = set(['php', 'gz', 'tar', 'rar'])

    # email config here
    EMAIL_SERVER = "email.sse.com.cn"
    EMAIL_SERVER_PORT = 465
    EMAIL_USER_ACCOUNT = "aiops@sse.com.cn"
    EMAIL_USER_PWD = "ChangeMe@sse"
    # sms config here
    SMS_API = "http://10.10.11.60:8080/msg/newmessage.do"
    SMS_ACCOUNT = "test4sms"
    SMS_PWD = "test4sms"
    # wechat config here
    TOKEN_URL = "https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={}&corpsecret={}"
    PUSH_URL = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={}"
    CORP_ID = "wx25d4842df1c1035f"
    AGENT_ID = "1000005"
    SECRET = "G-FCRXlHM3qOq--3Gs6Ki6zpq3IFEGh5gkY0MoNSgCQ"

    # application config
    APP_TYPES = [
        {'id': 1, 'label': u'转发'},
        {'id': 2, 'label': u'发布'},
        {'id': 3, 'label': u'中间件'},
        {'id': 4, 'label': u'数据库'} ]    # 1：转发，2：发布， 3：中间件， 4： 数据库
    APP_STATUS = [1, 2, 3, 4]     # 1: new , 2: modified, 3: published, 4: offline
    APP_LANGUAGES = ['JAVA', 'C', 'GO', 'SHELL']

    # CMDB config
    CMDB_HTTP_SCHEMA = "http"
    CMDB_HOST = "10.111.2.59"
    CMDB_PORT = 8083
    SUPPLIER_ACCOUNT = 0

    # Multiple Download Dir user ANSILBE TASK config defined
    MUL_DOWNLOAD_DIR = "/home/mds/aops/runner/mul_download"
    # Datetime format
    DATE_FORMAT = "%Y-%m-%d"

    MUL_DOWNLOAD_CACHE = '/home/mds/aops/mul_download_cache'


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://mds:Pwd@123@10.111.2.41:3306/aops'
    ENV = "production"


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False
    # SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://mds:Pwd@123@10.111.2.41:3306/aops'
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:Pwd@123@10.111.2.41:3306/fengli'

    GITLAB_URL = "http://10.111.2.41:8080"
    GITLAB_TOKEN = "MqGruzB2yzUGeo9PZM78"

    # redis config here
    REDIS_HOST = "10.111.2.41"
    REDIS_PORT = 6379
    REDIS_DB = 8

    # Scheduler config
    SCHEDULER_HTTP_SCHEMA = "http"
    SCHEDULER_HOST = "10.111.2.41"
    SCHEDULER_PORT = 5200

    # ftp config
    MUL_DOWNLOAD_DIR = "/home/mds/aops/runner"
    PRIVATE_KEY_PATH = '/home/mds/.ssh/id_rsa'
    FTP_SERVER = "10.111.2.41"
    FTP_SERVER_PORT = 2222
    FTP_SERVER_USER = "mds"


class TestingConfig(Config):
    TESTING = True
    ENV = "testing"
    PASSPORT_AUTH = True
    PASSPORT_AUDIT = True

    SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://mds:Pwd@123456@10.111.2.166:3306/aops'

    GITLAB_URL = "http://10.111.2.166:8080"
    GITLAB_TOKEN = "sfdLojvfp6yqWyzEsb3j"

    # redis config here
    REDIS_HOST = "10.111.2.166"
    REDIS_PORT = 6379
    REDIS_DB = 8

    # Scheduler config
    SCHEDULER_HTTP_SCHEMA = "http"
    SCHEDULER_HOST = "10.111.2.165"
    SCHEDULER_PORT = 5200

    # ftp config
    MUL_DOWNLOAD_DIR = "/home/mds/aops/runner/mul_download"
    PRIVATE_KEY_PATH = '/home/mds/.ssh/id_rsa'
    FTP_SERVER = "10.111.2.165"
    FTP_SERVER_PORT = 2222
    FTP_SERVER_USER = "mds"


configs = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig
}

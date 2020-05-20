#!/usr/bin/env python
# -*- coding:utf-8 -*-


class Error(Exception):
    def __init__(self, msg, code=500):
        self.msg = msg
        self.code = code
        Exception.__init__(self, self.msg)

    def to_dict(self):
        return dict(msg=self.msg, code=self.code)


class ResourceNotFoundError(Error):
    def __init__(self, obj, obj_id):
        self.msg = u"{} can't be found with ID {}".format(obj, obj_id)
        Error.__init__(self, self.msg, 404)


class ResourcesNotDisabledError(Error):
    def __init__(self, obj, obj_id):
        self.msg = u"{} not disabled with ID {}".format(obj, obj_id)
        Error.__init__(self, self.msg, 404)


class NotEnableError(Error):
    def __init__(self, obj, obj_id):
        self.msg = u"{} can't be enable with ID {}".format(obj, obj_id)
        Error.__init__(self, self.msg, 409)


class RequestError(Error):
    def __init__(self, api):
        self.msg = u"can't request with api {}".format(api)
        Error.__init__(self, self.msg, 403)


class NotFoundError(Error):
    def __init__(self, obj, obj_id):
        self.msg = u"{} can't be found with ID {}".format(obj, obj_id)
        Error.__init__(self, self.msg, 404)


class ResourcesNotFoundError(Error):
    def __init__(self, obj):
        self.msg = u"{} list can't be found, please check your params and try again".format(obj)
        Error.__init__(self, self.msg, 404)


class ResourceNotUpdatedError(Error):
    def __init__(self, obj):
        self.msg = u"{} can't be updated, please check your params and try again".format(obj)
        Error.__init__(self, self.msg, 404)

class ValidationError(Error):
    def __init__(self, msg):
        self.msg = u'Validation Error: {}'.format(msg)
        Error.__init__(self, self.msg)


class ResourceAlreadyExistError(Error):
    def __init__(self, obj):
        self.msg = u"{} item already exist with some unique fields".format(obj)
        Error.__init__(self, self.msg, 404)


class SchedulerError(Error):
    def __init__(self, msg):
        self.msg = u'Scheduler server occurred error: {}'.format(msg)
        Error.__init__(self, self.msg)


class CmdbError(Error):
    def __init__(self, msg):
        self.msg = u'CMDB server occurred error: {}'.format(msg)
        Error.__init__(self, self.msg)


class UserLoginError(Error):
    def __init__(self):
        self.msg = u'Username or password is not correct'
        Error.__init__(self, self.msg)


class NoTaskError(Error):
    def __init__(self, msg):
        self.msg = u'No tasks in the homework'.format(msg)
        Error.__init__(self, self.msg)


class ApprovalError(Error):
    def __init__(self, msg):
        self.msg = u'The task is under review'.format(msg)
        Error.__init__(self, self.msg)


class NoPermissionError(Error):
    def __init__(self, msg):
        self.msg = u'no permission'.format(msg)
        Error.__init__(self, self.msg)


class ConflictError(Error):
    def __init__(self, msg):
        self.msg = u'This resource has other resources to reuse'.format(msg)
        Error.__init__(self, self.msg)


class ApproveYourselfError(Error):
    def __init__(self, msg):
        self.msg = u'Cannot approve tasks created by yourself'.format(msg)
        Error.__init__(self, self.msg)


class ResourceNotEmptyError(Error):
    def __init__(self, obj):
        self.msg = u'Resource {} is not empty.'.format(obj)
        Error.__init__(self, self.msg, 409)


class EmailFailedError(Error):
    def __init__(self, msg):
        self.msg = u'Send email failed, reason: {}'.format(msg)
        Error.__init__(self, self.msg)


class SmsFailedError(Error):
    def __init__(self, msg):
        self.msg = u'Send sms failed, reason: {}'.format(msg)
        Error.__init__(self, self.msg)


class WechatFailedError(Error):
    def __init__(self, msg):
        self.msg = u'Send wechat failed, reason: {}'.format(msg)
        Error.__init__(self, self.msg)


class GitlabNotFoundError(Error):
    def __init__(self, obj, obj_args):
        self.msg = u"{} can't be found with params {}".format(obj, obj_args)
        Error.__init__(self, self.msg, 404)


class GitlabError(Error):
    def __init__(self, msg, code):
        self.msg = u"Gitlab occurred error: {}".format(msg)
        Error.__init__(self, self.msg, code)


class NotCommandWhiteListError(Error):
    def __init__(self):
        self.msg = u"Command white list is empty"
        Error.__init__(self, self.msg)


class MismatchError(Error):
    def __init__(self, args):
        self.msg = u"Command white list is mismatch: {}".format(args)
        Error.__init__(self, self.msg)


class NotFoundFtpFileError(Error):
    def __init__(self, server, file_name, msg):
        self.msg = u"Ftp server {} not exist file: {}, msg: {}".format(server, file_name, msg)
        Error.__init__(self, self.msg, code=404)
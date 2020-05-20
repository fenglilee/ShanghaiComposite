#!/usr/bin/env python
# -*- coding:utf-8 -*-


class TodoNotFound(Exception):
    def __init__(self, identifier):
        super(TodoNotFound, self).__init__()
        self.message = "TODO item can't be found with ID {}".format(identifier)


class TodosNotFound(Exception):
    def __init__(self, identifier):
        super(TodoNotFound, self).__init__()
        self.message = "TODO items can't be found,please check your params and try again".format(identifier)


class UserNotFound(Exception):
    def __init__(self, identifier):
        super(UserNotFound, self).__init__()
        self.message = "User can't be found with ID {}".format(identifier)


class RoleNotFound(Exception):
    def __init__(self, identifier):
        super(RoleNotFound, self).__init__()
        self.message = "Role can't be found with ID {}".format(identifier)


class UserConstraintNotFound(Exception):
    def __init__(self, identifier):
        super(UserConstraintNotFound, self).__init__()
        self.message = "User Constraint can't be found with ID {}".format(identifier)


class ResourceConstraintNotFound(Exception):
    def __init__(self, identifier):
        super(ResourceConstraintNotFound, self).__init__()
        self.message = "Resource Constraint can't be found with ID {}".format(identifier)

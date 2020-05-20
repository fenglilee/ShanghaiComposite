#!/usr/bin/env python
# # -*- coding:utf-8 -*-
import requests
import json
from aops.applications.exceptions.exception import Error


class Singleton(object):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            orig = super(Singleton, cls)
            cls._instance = orig.__new__(cls, *args, **kwargs)
        return cls._instance


class GitLabApiException(Exception):
    """"""


class GitLabApi(Singleton):
    def __init__(self, base_url, private_token):
        self.base_url = base_url
        self.headers = {'Accept': 'application/json', "PRIVATE-TOKEN": private_token}
        self.exception_class = GitLabApiException

    def get_url(self, endpoint):
        url = self.base_url + endpoint
        return url

    def get(self, endpoint):
        response = requests.get(self.get_url(endpoint), headers=self.headers)
        try:
            content = json.loads(response.text)
        except ValueError:
            content = {"ErrorMessage": response.text}
        return content, response.status_code

    def _facade(self, endpoint, method, data=None):
        function_map = {"GET": self.get}
        try:
            content, status_code = function_map[method](endpoint) if method == "GET" else function_map[method](
                endpoint, data)
            if status_code == 200:
                return content
            else:
                raise Error(content.get('ErrorMessage'))
        except self.exception_class as e:
            raise Error(e.message, code=410)

    def get_commits_list_by_path(self, project_id, path=None, ref_name='master'):
        if path:
            if path.startswith('/'):
                path = path[1:]
            endpoint = '/api/v4/projects/' + str(project_id) + '/repository/commits?ref_name=' + ref_name + '&path=' + path
        else:
            endpoint = '/api/v4/projects/' + str(project_id) + '/repository/commits?ref_name=' + ref_name
        return self._facade(endpoint, "GET")

    def get_last_commit_by_path(self, project_id, path=None, ref_name='master'):
        if path:
            if path.startswith('/'):
                path = path[1:]
            endpoint = '/api/v4/projects/' + str(project_id) + '/repository/commits?ref_name=' + ref_name + '&path=' + path
        else:
            endpoint = '/api/v4/projects/' + str(project_id) + '/repository/commits?ref_name=' + ref_name
        content = self._facade(endpoint, "GET")
        if len(content) > 0:
            return content[0]
        else:
            raise Error(u'此目录在此分支({})未存在提交记录'.format(ref_name), code=404)

#!/usr/bin/env python
# -*- coding:utf-8 -*-
import json

import pytest

from aops.applications.database.models.task.task import Task


class TestGetTasks(object):
    @classmethod
    def setup_class(cls):
        """ setup any state specific to the execution of the given class (which
        usually contains tests).
        """
        cls.name = 'test_name'
        cls.type = 'test_type'
        cls.language = 'test_language'
        cls.target_system = 'target_system'
        cls.description = 'description'
        cls.risk_level = 1
        cls.status = 'test_status'
        cls.approver = 'test_approver'
        cls.creator = 'test_creator'
        cls.is_enable = False
        cls.risk_statement = 'test_risk_statement'
        cls.time_out = 1
        cls.business_group = 'test_business_group'
        cls.script = 'test_script'
        cls.script_version = 'test_script_version'
        cls.project_id = 'test_project_id'
        cls.script_parameter = 'test_script_parameter'

        cls.per_page = 5
        cls.page = 1
        cls.error_page_num = 2

    @classmethod
    def teardown_class(cls):
        """ teardown any state that was previously setup with a call to
        setup_class.
        """
        print("tear down............")

    @pytest.fixture(scope="class", autouse=True)
    def prepare_to_add_task(self, app):
        with app.app_context():
            Task().create(name=self.name, type=self.type, language=self.language, target_system=self.target_system,
                          description=self.description, risk_level=self.risk_level, status=self.status,
                          approver=self.approver, creator=self.creator, is_enable=self.is_enable,
                          risk_statement=self.risk_statement, time_out=self.time_out, business_group=self.business_group
                          , script=self.script, script_version=self.script_version, project_id=self.project_id)

    def test_get_tasks(self, client):
        rv = client.get('/v1/tasks/?per_page={}&page={}'
                        .format(self.per_page, self.page), follow_redirects=True)
        result = json.loads(rv.data)
        assert len(result['items']) == 1
        re_task = result['items'][0]
        assert re_task['name'] == self.name
        assert result['page'] == self.page
        assert result['per_page'] == self.per_page

    def test_get_not_exist_tasks(self, client):
        result = client.get('/v1/tasks/?per_page={}&page={}'.format(self.per_page, self.error_page_num),
                            follow_redirects=True)
        assert result.status_code == 404
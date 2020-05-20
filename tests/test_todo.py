# #!/usr/bin/env python
# -*- coding:utf-8 -*-
import json

import pytest

from aops.applications.database.models.todo import Todo


class TestGetTodos(object):
    @classmethod
    def setup_class(cls):
        """ setup any state specific to the execution of the given class (which
        usually contains tests).
        """
        cls.name = 'test_name'
        cls.email = 'test_email'
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
    def prepare_to_add_todo(self, app):
        with app.app_context():
            Todo().create(name=self.name, email=self.email)

    def test_get_todos(self, client):
        rv = client.get('/v1/todos/?per_page={}&page={}'.format(self.per_page, self.page), follow_redirects=True)
        result = json.loads(rv.data)
        assert len(result['items']) == 1
        re_todo = result['items'][0]
        assert re_todo['name'] == self.name
        assert re_todo['email'] == self.email
        assert result['page'] == self.page
        assert result['per_page'] == self.per_page

    def test_get_not_exist_todos(self, client):
        result = client.get('/v1/todos/?per_page={}&page={}'.format(self.per_page, self.error_page_num),
                            follow_redirects=True)
        assert result.status_code == 404


class TestPostTodos(object):
    @classmethod
    def setup_class(cls):
        cls.name = 'test_name'
        cls.email = 'test_email'

    def test_post_todos(self, client):
        rv = client.post('/v1/todos/', follow_redirects=True, data={
            "name": self.name,
            "email": self.email
        })
        result = json.loads(rv.data)
        assert result['name'] == self.name
        assert result['email'] == self.email


class TestGetTodo(object):
    @classmethod
    def setup_class(cls):
        cls.name = 'test_name'
        cls.email = 'test_email'
        cls.todo_id = 1
        cls.not_exist_todo_id = 10

    @pytest.fixture(scope="class", autouse=True)
    def prepare_to_add_todo(self, app):
        with app.app_context():
            Todo().create(name=self.name, email=self.email)

    def test_get_todo(self, client):
        rv = client.get('/v1/todos/{}'.format(self.todo_id), follow_redirects=True)
        result = json.loads(rv.data)
        assert result['name'] == self.name
        assert result['email'] == self.email

    def test_get_not_exist_todo(self, client):
        rv = client.get('/v1/todos/{}'.format(self.not_exist_todo_id), follow_redirects=True)
        assert rv.status_code == 404


class TestDeleteTodo(object):
    @classmethod
    def setup_class(cls):
        cls.name = 'test_name'
        cls.email = 'test_email'
        cls.todo_id = 1
        cls.not_exist_todo_id = 10

    @pytest.fixture(scope="class", autouse=True)
    def prepare_to_add_todo(self, app):
        with app.app_context():
            Todo().create(name=self.name, email=self.email)

    def test_delete_todo(self, client):
        result = client.delete('/v1/todos/{}'.format(self.todo_id), follow_redirects=True)
        assert result.status_code == 200
        result = client.get('/v1/todos/{}'.format(self.todo_id), follow_redirects=True)
        assert result.status_code == 404

    def test_delete_not_exist_todo(self, client):
        result = client.delete('/v1/todos/{}'.format(self.not_exist_todo_id), follow_redirects=True)
        assert result.status_code == 404


class TestPutTodo(object):
    @classmethod
    def setup_class(cls):
        cls.origin_name = 'origin_name'
        cls.name = 'test_name'
        cls.origin_email = 'origin_email'
        cls.email = 'test_email'
        cls.todo_id = 1
        cls.not_exist_todo_id = 10

    @pytest.fixture(scope="class", autouse=True)
    def prepare_to_add_todo(self, app):
        with app.app_context():
            Todo().create(name=self.origin_name, email=self.origin_email)

    def test_put_todo(self, client):
        rv = client.put('/v1/todos/{}'.format(self.todo_id), follow_redirects=True, data={
            "name": self.name,
            "email": self.email
        })
        assert rv.status_code == 200
        result = json.loads(rv.data)
        assert result['name'] == self.name
        assert result['email'] == self.email

    def test_put_not_exist_todo(self, client):
        result = client.put('/v1/todos/{}'.format(self.not_exist_todo_id), follow_redirects=True, data={
            "name": self.name,
            "email": self.email
        })
        assert result.status_code == 404

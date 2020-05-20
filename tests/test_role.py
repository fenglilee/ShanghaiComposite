# #!/usr/bin/env python
# # -*- coding:utf-8 -*-
# # @Time    : 18-6-25 下午9:24
# # @Author  : Hbs
# import json
#
# import pytest
#
# from aops.applications.database.models import Role, Permission
#
#
# class TestGetRoles(object):
#     @classmethod
#     def setup_class(cls):
#         """setup any state specific to the execution of the given class (which
#         usually contains tests).
#         """
#         cls.name = 'test_name'
#         cls.info = 'test_info'
#
#     @classmethod
#     def teardown_class(cls):
#         """ teardown any state that was previously setup with a call to
#         setup_class.
#         """
#         print('tear down......')
#
#     @pytest.fixture(scope='class', autouse=True)
#     def prepare_to_add_role(self, app):
#         """
#         Args:
#             app: This app is called from the conftest.py
#         """
#         with app.app_context():
#             Role().create(role_name=self.name, role_info=self.info)
#
#     def test_get_roles(self, client):
#         """Start with a blank database."""
#         rv = client.get('/v1/roles', follow_redirects=True)
#         roles = json.loads(rv.data)
#         assert len(roles) == 1
#         role = roles[0]
#         assert role['role_name'] == self.name
#         assert role['role_info'] == self.info
#
#
# class TestPostRoles(object):
#     @classmethod
#     def setup_class(cls):
#         """setup any state specific to the execution of the given class (which
#         usually contains tests).
#         """
#         cls.name = 'test_name'
#         cls.info = 'test_info'
#
#     def test_post_roles(self, client):
#         """Start with a blank database."""
#         rv = client.post('/v1/roles/', follow_redirects=True, data={
#             "role_name": self.name,
#             "role_info": self.info
#         })
#         role = json.loads(rv.data)
#         assert role['role_name'] == self.name
#         assert role['role_info'] == self.info
#
#
# class TestDeleteRole(object):
#     @classmethod
#     def setup_class(cls):
#         """ setup any state specific to the execution of the given class (which
#                 usually contains tests).
#                 """
#         cls.name = 'test_name'
#         cls.info = 'test_info'
#         cls.role_id = 1
#         cls.not_exist_role_id = 10
#
#     @pytest.fixture(scope='class', autouse=True)
#     def prepare_to_add_role(self, app):
#         """
#         Args:
#             app: This app is called from the conftest.py
#         """
#         with app.app_context():
#             Role().create(role_name=self.name, role_info=self.info)
#
#     def test_delete_role(self, client):
#         """Start with a blank database."""
#         result = client.delete('/v1/roles/{}'.format(self.role_id), follow_redirects=True)
#         assert result.status_code == 200
#         result = client.get('/v1/todos/{}'.format(self.role_id), follow_redirects=True)
#         assert result.status_code == 404
#
#     def test_delete_not_exist_role(self, client):
#         """Start with a blank database."""
#         result = client.delete('/v1/roles/{}'.format(self.not_exist_role_id), follow_redirects=True)
#         assert result.status_code == 404
#
#
# class TestPutRole(object):
#     @classmethod
#     def setup_class(cls):
#         """ setup any state specific to the execution of the given class (which
#                 usually contains tests).
#                 """
#         cls.name = 'test_name'
#         cls.info = 'test_info'
#         cls.update_name = 'update_name'
#         cls.role_id = 1
#         cls.not_exist_role_id = 10
#
#     @pytest.fixture(scope='class', autouse=True)
#     def prepare_to_add_role(self, app):
#         """
#         Args:
#             app: This app is called from the conftest.py
#         """
#         with app.app_context():
#             Role().create(role_name=self.name, role_info=self.info)
#
#     def test_put_role(self, client):
#         """Start with a blank database."""
#         rv = client.put('/v1/roles/{}'.format(self.role_id), follow_redirects=True, data={
#             "role_name": self.update_name,
#             "role_info": self.info
#         })
#         assert rv.status_code == 200
#         result = json.loads(rv.data)
#         assert result['role_name'] == self.update_name
#         assert result['role_info'] == self.info
#
#     def test_put_not_exist_todo(self, client):
#         """Start with a blank database."""
#         result = client.put('/v1/todos/{}'.format(self.not_exist_role_id), follow_redirects=True, data={
#             "role_name": self.name,
#             "role_info": self.info
#         })
#         assert result.status_code == 404
#
#
# class TestGetPermissions(object):
#     @classmethod
#     def setup_class(cls):
#         """setup any state specific to the execution of the given class (which
#         usually contains tests).
#         """
#         cls.permission_name = 'test_permission_name'
#         cls.resource_type_name = 'test_resource_type_name'
#         cls.operator_name = 'test_operator_name'
#
#     @classmethod
#     def teardown_class(cls):
#         """ teardown any state that was previously setup with a call to
#         setup_class.
#         """
#         print('tear down......')
#
#     @pytest.fixture(scope='class', autouse=True)
#     def prepare_to_add_permission(self, app):
#         """
#         Args:
#             app: This app is called from the conftest.py
#         """
#         with app.app_context():
#             Permission().create(permission_name=self.permission_name, resource_type_name=self.resource_type_name, operator_name=self.operator_name)
#
#     def test_get_permissions(self, client):
#         """Start with a blank database."""
#         rv = client.get('/v1/roles/permission', follow_redirects=True)
#         result = json.loads(rv.data)
#         assert len(result) == 1
#         permission = result[0]
#         assert permission['permission_name'] == self.permission_name
#         assert permission['resource_type_name'] == self.resource_type_name
#         assert permission['operator_name'] == self.operator_name
#
#
# class TestGetRolePermissions(object):
#     @classmethod
#     def setup_class(cls):
#         """setup any state specific to the execution of the given class (which
#         usually contains tests).
#         """
#         cls.permission_name = 'test_permission_name'
#         cls.resource_type_name = 'test_resource_type_name'
#         cls.operator_name = 'test_operator_name'
#
#     @classmethod
#     def teardown_class(cls):
#         """ teardown any state that was previously setup with a call to
#         setup_class.
#         """
#         print('tear down......')
#
#     @pytest.fixture(scope='class', autouse=True)
#     def prepare_to_add_permission(self, app):
#         """
#         Args:
#             app: This app is called from the conftest.py
#         """
#         with app.app_context():
#             Permission().create(permission_name=self.permission_name, resource_type_name=self.resource_type_name, operator_name=self.operator_name)
#
#     def test_get_permissions(self, client):
#         """Start with a blank database."""
#         rv = client.get('/v1/roles/permission', follow_redirects=True)
#         result = json.loads(rv.data)
#         assert len(result) == 1
#         permission = result[0]
#         assert permission['permission_name'] == self.permission_name
#         assert permission['resource_type_name'] == self.resource_type_name
#         assert permission['operator_name'] == self.operator_name
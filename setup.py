#!/usr/bin/env python
# -*- coding:utf-8 -*-

from setuptools import find_packages, setup

setup(
    name='aops',
    version='0.0.1',
    description="Auto operating platform",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Flask==1.0.2',
        'Flask-Migrate==2.2.0',
        'flask-restplus==0.11.0',
        'Flask-SQLAlchemy==2.3.2',
        'flask-restplus==0.11.0',
        'flower==0.9.2',
        'celery==3.1.25',
        'coverage==4.5.1',
        'enum34==1.1.6',
        'eventlet==0.23.0',
        'greenlet==0.4.13',
        'gunicorn==19.8.1',
        'mysql-connector-python==8.0.11',
        'pbkdf2==1.3',
        'pydevd==1.2.0',
        'pytest==3.6.1',
        'redis==2.10.6',
        'GitPython==2.1.10',
        'python-gitlab==1.5.1'
    ],
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    test_suite='tests'
)
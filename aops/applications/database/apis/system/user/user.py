#!/usr/bin/env python
# -*- coding:utf-8 -*-

import re
import hashlib
import datetime
import pbkdf2

import json
from flask import session

from redis import StrictRedis
from sqlalchemy import desc, or_
from sqlalchemy.orm.exc import NoResultFound
from aops.applications.exceptions.exception import ValidationError
from aops.applications.database.models.system.user import User
from aops.applications.database.models import SysConfigBusiness
from aops.applications.database.apis.user_permission.role import get_role_with_id
from aops.applications.exceptions.exception import ResourceNotFoundError
from aops.applications.exceptions.exception import UserLoginError
from flask import current_app as app

SALT = 'AOPS'
error_pattern = re.compile(
    """^Validation Error: \(mysql.connector.errors.IntegrityError\) 1062 \(23000\): Duplicate entry (?P<content>.*?) for key (?P<key>.*?) (.*)'"""
)


def get_users_list(page, per_page, username=None, business=None, status=None, fuzzy_query=None):

    users = User.query.filter_by(is_deleted=False). \
        order_by(desc(User.updated_at))

    # Precise query
    if username:
        users = users.filter(User.username.like("%{}%".format(username)))
    if business:
        users = users.filter(User.business.like("%{}%".format(business)))

    if status:
        users = users.filter(User.status.like("%{}%".format(status)))

    # Fuzzy query
    if fuzzy_query:
        fuzzy_str = ''.join([User.username, User.business, User.status])
        users = users.filter(fuzzy_str.like("%{}%".format(fuzzy_query)))

    # return pagination body
    try:
        user_set = users.paginate(page=page, per_page=per_page)
        for user in user_set.items:
            add_user_attribute(user)
        return user_set
    except Exception as e:
        raise ResourceNotFoundError('User', e.message)


def get_business_with_id(identifier):
    try:
        business_config = SysConfigBusiness.query.filter_by(id=identifier, is_deleted=False).one()
    except NoResultFound:
        raise ResourceNotFoundError('BusinessConfig', identifier)
    return business_config


def get_business_with_name(name):
    try:
        business_config = SysConfigBusiness.query.filter_by(name=name, is_deleted=False).one()
    except NoResultFound:
        raise ResourceNotFoundError('BusinessConfig', name)
    return business_config


def create_user(args):
    roles = [get_role_with_id(role_id) for role_id in args.role_ids]
    businesses = [get_business_with_id(business_id) for business_id in args.business_ids]
    modified_by = session.get('user_info').get('user')

    delete_user = User.query.filter_by(username=args.username, is_deleted=True).first()
    if delete_user is not None:
        raise ValidationError("username {} has been disabled, can not be used any more".format(args.username))

    try:
        user = User.create(
            username=args.username,
            password=gen_password_hash(args.password),
            realname=args.realname,
            wechat=args.wechat,
            businesses=businesses,
            email=args.email,
            telephone=args.telephone,
            status=args.status,
            modified_by=modified_by,
            roles=roles
        )
        return user.to_dict()
    except ValidationError as e:
        re_res = re.search(error_pattern, e.msg)
        raise ValidationError('{} {} has already existed'.format(re_res.group('key'), re_res.group('content')))


def create_default_user(**kwargs):
    kwargs.update(password=gen_password_hash(kwargs.get('password', 'admin')))
    return User.create_if_not_exist(**kwargs)


def gen_password_hash(password):
    return pbkdf2.crypt(password, SALT)


def get_user_with_id(identifier):
    # if attr is unique, should use first_or_404() function instead of one() function
    try:
        user = User.query.filter_by(id=identifier, is_deleted=False).first()
        add_user_attribute(user)
    except NoResultFound:
        raise ResourceNotFoundError('User', identifier)

    return user


def get_users_with_ids(ids):
    try:
        users = User.query.filter(User.id.in_(ids), User.is_deleted.is_(False)).all()
    except NoResultFound:
        raise ResourceNotFoundError('User', ids)

    return users


def get_users_with_names(names):
    try:
        users = User.query.filter(User.username.in_(names), User.is_deleted.is_(False)).all()
    except NoResultFound:
        raise ResourceNotFoundError('User', names)

    return users


def get_user_with_name(username):
    try:
        user = User.query.filter_by(username=username, is_deleted=False).first()
    except NoResultFound:
        raise ResourceNotFoundError('User', username)

    return user


def check_user_password(username, password):
    """
    Args:
        username (str)
        password (str) - plain-text password

    Returns:
        user (User) - if there is a user with a specified username and
        password, None otherwise.
    """

    host = app.config.get("REDIS_HOST")
    port = app.config.get("REDIS_PORT")
    db = app.config.get("REDIS_DB")
    redis_manager = RedisManager(host=host, port=port, db=db)
    login_record = redis_manager.get(key=username)
    if login_record is not None and login_record['block']:
        raise ValidationError("Present account has been forbidden for one hour")

    hash_password = gen_password_hash(password)
    user = User.query.filter_by(username=username, is_deleted=False).first()
    if user is not None and user.status == 0:
        raise ValidationError("Present user is not enabled yet")
    if user is None or user.password != hash_password:
        if login_record is None:
            login_record = dict(count=1, block=False)
        else:
            login_record['count'] += 1
            if login_record['count'] >= 5:
                login_record['block'] = True
        redis_manager.set(key=username, data=login_record)
        raise UserLoginError()
    return user


def delete_user_with_id(identifier):
    user = User.query.filter_by(id=identifier, is_deleted=False).first()
    return user.update(**{'deleted_at': datetime.datetime.now(), 'is_deleted': True})


def delete_users_with_ids(identifiers):
    deleted_users = []
    for identifier in identifiers:
        deleted_users.append(delete_user_with_id(identifier))

    return deleted_users


def update_user_with_id(identifier, user_info):

    user_info = {key: value for key, value in user_info.iteritems() if value is not None}
    if 'role_ids' in user_info:
        role_ids = user_info.pop('role_ids')
        if role_ids is not None:
            roles = [get_role_with_id(role_id) for role_id in role_ids]
            user_info.update(roles=roles)
    if 'business_ids' in user_info:
        business_ids = user_info.pop('business_ids')
        if business_ids is not None:
            businesses = [get_business_with_id(business_id) for business_id in business_ids]
            user_info.update(businesses=businesses)

    user_info.update(
        id=identifier,
        updated_at=datetime.datetime.now()
    )
    user = User.query.filter_by(id=identifier, is_deleted=False).first()
    if user is None:
        raise ResourceNotFoundError('User', identifier)
    user = user.update(**user_info)
    add_user_attribute(user)
    return user


class PwdCheck(object):

    def __init__(self, length=8, upper=True, lower=True, special=True):
        self._length = length
        self._upper = upper
        self._lower = lower
        self._special = special

    def _check_length(self, password):
        length = len(password)
        assert length >= self._length, 'password should contain at least %s characters' % (self._length,)

    def _check_upper(self, password):
        if self._upper:
            pattern = re.compile('[A-Z]+')
            match = pattern.findall(password)
            assert len(match) > 0, 'password should contain capital letters'

    def _check_lower(self, password):
        if self._lower:
            pattern = re.compile('[a-z]+')
            match = pattern.findall(password)
            assert len(match) > 0, 'password should contain lowercase letters'

    def _check_special(self, password):
        if self._special:
            pattern = re.compile('([^a-z0-9A-Z])+')
            match = pattern.findall(password)
            assert len(match) > 0, 'password should contain special characters'

    def validate_password(self, password):
        try:
            self._check_length(password=password)
            self._check_upper(password=password)
            self._check_lower(password=password)
            self._check_special(password=password)
        except AssertionError as e:
            raise ValidationError(e.message)


def get_all_users():
    try:
        users = User.query.filter_by(is_deleted=False).order_by(desc(User.updated_at))
        return users.all()
    except Exception as e:
        raise ResourceNotFoundError('User', '{}'.format(e))


class RedisManager(object):

    def __init__(self, host=None, port=None, db=None, timeout=3600, **kwargs):
        self._redis = StrictRedis(host=host, port=port, db=db, **kwargs)
        self._timeout = timeout

    @staticmethod
    def _generate_key(key="test"):
        return hashlib.sha256(key).hexdigest()

    def get(self, key="test"):
        redis_key = self._generate_key(key=key)
        data = self._redis.get(redis_key)
        if data is None:
            return data
        return json.loads(data)

    def set(self, key="test", data=None):
        redis_key = self._generate_key(key=key)
        self._redis.setex(redis_key, self._timeout, json.dumps(data))


def add_user_attribute(user):
    role_ids = [role.id for role in user.roles]
    business_ids = [businesses.id for businesses in user.businesses]
    role_names = [role.name for role in user.roles]
    business_names = [businesses.name for businesses in user.businesses]
    setattr(user, 'role_ids', role_ids)
    setattr(user, 'business_ids', business_ids)
    setattr(user, 'role_names', role_names)
    setattr(user, 'business_names', business_names)


class UsernameCheck(object):

    def __init__(self, pattern=re.compile('[^a-zA-Z0-9_-]')):
        self._pattern = pattern

    def validate_username(self, username=None):
        try:
            match = self._pattern.findall(username)
            assert len(match) == 0, 'username contains other characters except letters, numbers, "-" and "-"'
        except AssertionError as e:
            raise ValidationError(e.message)


def get_raw_user_with_id(identifier):
    # if attr is unique, should use first_or_404() function instead of one() function
    try:
        user = User.query.filter_by(id=identifier, is_deleted=False).one()
    except NoResultFound:
        raise ResourceNotFoundError('User', identifier)

    return user













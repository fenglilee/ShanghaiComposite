#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 18-7-4 上午10:38
# @Author  : szf

from sqlalchemy import desc
from sqlalchemy.orm.exc import NoResultFound

from aops.applications.database.models.resource.host import HostAccount as Account
from aops.applications.exceptions.exception import ResourceNotFoundError


def get_account_list(username=None, fuzzy_query=None):
    """
    Get all accounts items
    args:
        username: precise query
        fuzzy_query: fuzzy query applied for username and description
    Returns:
        account list
    """
    accounts = Account.query.filter_by(is_deleted=False). \
        order_by(desc(Account.updated_at))

    # Precise query
    if username:
        accounts = accounts.filter(Account.username.like("%{}%".format(username)))

    # Fuzzy query example
    if fuzzy_query:
        fuzzy_str = ''.join([Account.username, Account.others])
        accounts = accounts.filter(fuzzy_str.like("%{}%".format(fuzzy_query)))

    return accounts.all()


def create_account(args):
    """
    Create a account with args
    Args:
        args: dict which contain (username, password, description)

    Returns:
        the created account
    """
    # account = Account.query.filter_by(username=args.username).first()
    # if account and not account.is_deleted:
    #     return 403     # this Account exists in db
    #
    # if account and account.is_deleted:
    #     account.Account_name = account.username + '_is_deleted_' + str(account.id)

    # the username maybe not unique
    account = Account.create(username=args.username, password=args.password)

    return account.to_dict()


def create_accounts(accounts):
    """ create multiple account"""
    results = []
    for args in accounts:
        account = Account.create(username=args['username'], password=args['password'])
        results.append(account)

    return results


def get_account_with_id(identifier):
    """
    Get a account with identifier
    Args:
        identifier: ID for Account item

    Returns:
        Just the account item with this ID

    Raises:
          ResourceNotFoundError: account is not found
    """
    try:
        account = Account.query.filter_by(id=identifier, is_deleted=False).one()
    except NoResultFound:
        raise ResourceNotFoundError('Account', identifier)
    return account


def delete_account_with_id(identifier):
    """
    Delete a account with identifier
    Args:
        identifier: ID for Account item

    Returns:
        Just the Account item with this ID.
    """
    return Account.soft_delete_by(id=identifier)


def update_account_with_id(identifier, account_info):
    """
    Update a Account with identifier
    Args:
        identifier: ID for Account item
        account_info: update Account with this info

    Returns:
        Just the Account item with this ID.
    """
    account_info.update(id=identifier)
    account = Account.query.filter_by(id=identifier, is_deleted=False).first()
    if account is None:
        raise ResourceNotFoundError('Account', identifier)
    return Account.update(**account_info)
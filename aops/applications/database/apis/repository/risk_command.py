#!/usr/bin/env python
# -*- coding:utf-8 -*-
from datetime import datetime
from sqlalchemy.orm.exc import NoResultFound
from flask import current_app as app
from aops.applications.database.models.repository.risk_command import RiskRepository, CommandWhiteList
from aops.applications.exceptions.exception import ResourceNotFoundError, ResourcesNotFoundError, ValidationError, \
    ResourceAlreadyExistError


def get_risk_repository_list(page, per_page, name=None, risk_level=None, creator=None, start_time=None, end_time=None, fuzzy_query=None):
    """
    Get all file review items
    Returns:
        file review items list
    """
    q = RiskRepository.query.filter_by(is_deleted=False).order_by(RiskRepository.updated_at.desc())

    if name:
        q = q.filter(RiskRepository.name.like("%{}%".format(name)))

    date_format = app.config.get("DATE_FORMAT")
    if start_time:
        start_time = datetime.strptime(start_time, date_format)
        q = q.filter(RiskRepository.created_at >= ("{}".format(start_time)))

    if end_time:
        end_time = datetime.strptime(end_time, date_format)
        q = q.filter(RiskRepository.updated_at <= ("{}".format(end_time)))

    if risk_level:
        q = q.filter(RiskRepository.risk_level == ("{}".format(risk_level)))

    if creator:
        q = q.filter(RiskRepository.creator.like(u"%{}%".format(creator)))

    if fuzzy_query:
        q = q.filter(RiskRepository.name.concat(RiskRepository.comment).like("%{}%".format(fuzzy_query)))

    try:
        return q.paginate(page=page, per_page=per_page)
    except Exception as e:
        app.logger.error("RiskRepository list failed: " + str(e))
        raise ResourcesNotFoundError("RiskRepositorys")


def get_risk_repository_list_search(name=None, creator=None):
    q = RiskRepository.query.filter_by(is_deleted=False).order_by(RiskRepository.updated_at.desc())
    if name:
        q = q.filter(RiskRepository.name.like("%{}%".format(name)))
    if creator:
        q = q.filter(RiskRepository.creator.like(u"%{}%".format(creator)))
    try:
        return q.all()
    except Exception as e:
        app.logger.error("RiskRepository list failed: " + str(e))
        raise ResourcesNotFoundError("RiskRepositorys")


def get_risk_repository_with_id(identifier):
    try:
        item = RiskRepository.query.filter_by(id=identifier, is_deleted=False).one()
    except NoResultFound:
        raise ResourceNotFoundError('RiskRepository', identifier)
    return item


def delete_task_with_id(identifier):
    item = get_risk_repository_with_id(identifier)
    return item.update(is_deleted=True, deleted_at=datetime.now())


def delete_risk_repository_with_ids(args):
    """
    Get a review with identifier
    Args:
        args: task review item ID

    Returns:
        Just the task review item with this ID
    """
    ids = args.ids
    return [delete_task_with_id(identifier) for identifier in ids]


def update_risk_repository_with_id(identifier, update_info):
    """
    Get a review with identifier
    Args:
        identifier:  item ID
        update_info:

    Returns:
        Just the item with this ID
    """
    item = get_risk_repository_with_id(identifier)
    update_info.update(
        id=identifier,
        updated_at=datetime.now()
    )

    return item.update(**update_info)


def create_risk_repository(args):
    """Create a item with args

    Args:
        args: dict which contain name, age, email

    Returns:
        Just the create item.
    """
    try:
        todo = RiskRepository.create(**args)
    except ValidationError:
        raise ResourceAlreadyExistError("Risk_command_repository")
    return todo.to_dict()


"""
command whiteList
"""


def get_command_whitelist_list(page, per_page, name=None, creator=None, start_time=None, end_time=None, fuzzy_query=None):
    """
    Get all file review items
    Returns:
        file review items list
    """
    q = CommandWhiteList.query.filter_by(is_deleted=False).order_by(CommandWhiteList.updated_at.desc())

    if name:
        q = q.filter(CommandWhiteList.name.like("%{}%".format(name)))

    date_format = app.config.get("DATE_FORMAT")
    if start_time:
        start_time = datetime.strptime(start_time, date_format)
        q = q.filter(CommandWhiteList.created_at >= ("{}".format(start_time)))

    if end_time:
        end_time = datetime.strptime(end_time, date_format)
        q = q.filter(CommandWhiteList.updated_at <= ("{}".format(end_time)))

    if creator:
        q = q.filter(CommandWhiteList.creator.like(u"%{}%".format(creator)))

    if fuzzy_query:
        q = q.filter(CommandWhiteList.name.concat(CommandWhiteList.comment).like("%{}%".format(fuzzy_query)))

    try:
        return q.paginate(page=page, per_page=per_page)
    except Exception as e:
        app.logger.error("CommandWhiteList list failed: " + str(e))
        raise ResourcesNotFoundError("CommandWhiteLists")


def get_whitelist_search(name=None, creator=None):
    q = CommandWhiteList.query.filter_by(is_deleted=False).order_by(CommandWhiteList.updated_at.desc())
    if name:
        q = q.filter(CommandWhiteList.name.like("%{}%".format(name)))
    if creator:
        q = q.filter(CommandWhiteList.creator.like(u"%{}%".format(creator)))
    try:
        return q.all()
    except Exception as e:
        app.logger.error("CommandWhiteList list failed: " + str(e))
        raise ResourcesNotFoundError("CommandWhiteList")


def get_command_whitelist_with_id(identifier):
    try:
        item = CommandWhiteList.query.filter_by(id=identifier, is_deleted=False).one()
    except NoResultFound:
        raise ResourceNotFoundError('CommandWhiteList', identifier)
    return item


def delete_command_whitelist_with_id(identifier):
    item = get_command_whitelist_with_id(identifier)
    return item.update(is_deleted=True, deleted_at=datetime.now())


def delete_command_whitelist_with_ids(args):
    """
    Get a review with identifier
    Args:
        args: task review item ID

    Returns:
        Just the task review item with this ID
    """
    ids = args.ids
    return [delete_command_whitelist_with_id(identifier) for identifier in ids]


def update_command_whitelist_with_id(identifier, update_info):
    """
    Get a review with identifier
    Args:
        identifier:  item ID
        update_info:

    Returns:
        Just the item with this ID
    """
    item = get_command_whitelist_with_id(identifier)
    update_info.update(
        id=identifier,
        updated_at=datetime.now()
    )

    return item.update(**update_info)


def create_command_whitelist(args):
    """Create a item with args

    Args:
        args: dict which contain name, age, email

    Returns:
        Just the create item.
    """
    try:
        command_whitelist = CommandWhiteList.create(**args)
    except ValidationError:
        raise ResourceAlreadyExistError("Command_whitelist")
    return command_whitelist.to_dict()

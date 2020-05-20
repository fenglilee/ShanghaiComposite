#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 18-7-13 上午10:38
# @Author  : szf

from sqlalchemy.orm.exc import NoResultFound

from aops.applications.database.models import AppParameter as Parameter
from aops.applications.exceptions.exception import ResourceNotFoundError


def create_parameter(args):
    """
    Create a parameter with args
    Args:
        args: dict which contain (username, password, description)

    Returns:
        the created parameter
    """
    parameter = Parameter.create(name=args.name, value=args.value)

    return parameter.to_dict()


def create_parameters(parameters):
    """ create multiple parameters"""
    results = []
    for args in parameters:
        param = Parameter.create(name=args.name, value=args.value)
        results.append(param)

    return results


def get_parameter_with_id(identifier):
    """
    Get a parameter with identifier
    Args:
        identifier: ID for Parameter item

    Returns:
        Just the parameter item with this ID

    Raises:
          ResourceNotFoundError: parameter is not found
    """
    try:
        parameter = Parameter.query.filter_by(id=identifier, is_deleted=False).one()
    except NoResultFound:
        raise ResourceNotFoundError('Parameter', identifier)
    return parameter


def delete_parameter_with_id(identifier):
    """
    Delete a parameter with identifier
    Args:
        identifier: ID for Parameter item

    Returns:
        Just the Parameter item with this ID.
    """
    return Parameter.soft_delete_by(id=identifier)


def update_parameter_with_id(identifier, parameter_info):
    """
    Update a Parameter with identifier
    Args:
        identifier: ID for Parameter item
        parameter_info: update Parameter with this info

    Returns:
        Just the Parameter item with this ID.
    """
    parameter_info.update(id=identifier)
    parameter = Parameter.query.filter_by(id=identifier, is_deleted=False).first()
    if parameter is None:
        raise ResourceNotFoundError('Parameter', identifier)
    return Parameter.update(**parameter_info)
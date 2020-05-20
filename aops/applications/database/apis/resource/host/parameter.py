#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 18-7-13 上午10:38
# @Author  : szf

from sqlalchemy import desc
from sqlalchemy.orm.exc import NoResultFound

from aops.applications.database.models.resource.host import  HostParameter as Parameter
from aops.applications.exceptions.exception import ResourceNotFoundError


def get_parameter_list(pkey=None, fuzzy_query=None):
    """
    Get all parameters items
    args:
        pkey: precise query for parameter key
        fuzzy_query: fuzzy query applied for parameter key and description
    Returns:
        parameter list
    """
    parameters = Parameter.query.filter_by(is_deleted=False). \
        order_by(desc(Parameter.updated_at))

    # Precise query
    if pkey:
        parameters = parameters.filter(Parameter.pkey.like("%{}%".format(pkey)))

    # Fuzzy query example
    if fuzzy_query:
        fuzzy_str = ''.join([Parameter.username, Parameter.others])
        parameters = parameters.filter(fuzzy_str.like("%{}%".format(fuzzy_query)))

    return parameters.all()


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
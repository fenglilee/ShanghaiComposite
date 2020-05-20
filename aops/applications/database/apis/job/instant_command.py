#!/usr/bin/env python
# -*- coding:utf-8 -*-
import json

from flask import request, session

from aops.applications.common.scheduler_request import SchedulerApi
from aops.applications.database.apis.resource.host.host import get_host_ips_with_ids
from aops.applications.database.models.repository.risk_command import CommandWhiteList
from aops.applications.exceptions.exception import NotCommandWhiteListError, MismatchError


def carry_out_command(args):

    business_group = request.cookies.get('BussinessGroup')
    login_name = session.get('user_info').get('user')

    command_white_list = CommandWhiteList.query.filter_by(is_deleted=False, business_group=business_group).all()
    if command_white_list:
        white_command = [command.name for command in command_white_list]
    else:
        raise NotCommandWhiteListError

    if args.command not in white_command:
        raise MismatchError(args.command)

    target_ip = get_host_ips_with_ids(args.target_ip)

    command_info = {
            'target_ip': target_ip,
            'command': args.command,
            'execution_account': args.execution_account,
            'creator': login_name,
            'business_group': business_group,
        }
    command_info = json.dumps(command_info)

    data = {'command_info': command_info}
    return SchedulerApi('/v1/command/').post(data=data)

def get_instant_command_record(page, per_page, ip):
        """
        Get all record
        :return:
             record list
        """
        creator = session.get('user_info').get('user')
        data = {
            'page': page,
            'per_page': per_page,
            'creator': creator,
            'ip': ip,
        }
        return SchedulerApi('/v1/command/').get(params=data)



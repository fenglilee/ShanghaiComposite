# !/usr/bin/python
# -*- coding:utf-8 -*-

"""
@author: fengli
@time: 2018/8/9 下午1:39
@file: message_center
"""

import smtplib
import requests
from email.header import Header
from email.mime.text import MIMEText
from aops.conf.server_config import Config
from aops.applications.lib.email_tmp import Email_Tmp_Top
from aops.applications.lib.email_tmp import Email_Tmp_Foot
from aops.applications.exceptions.exception import EmailFailedError
from aops.applications.exceptions.exception import SmsFailedError
from aops.applications.exceptions.exception import WechatFailedError


"""email config info here"""
_EmailServer = getattr(Config, 'EMAIL_SERVER', None)
_EmailServerPort = getattr(Config, 'EMAIL_SERVER_PORT', None)
_EmailUserAccount = getattr(Config, 'EMAIL_USER_ACCOUNT', None)
_EmailUserPwd = getattr(Config, 'EMAIL_USER_PWD', None)

"""sms config info here"""
_SmsAPI = getattr(Config, 'SMS_API', None)
_SmsAccount = getattr(Config, 'SMS_ACCOUNT', None)
_SmsPwd = getattr(Config, 'SMS_PWD', None)

"""wechat config info here"""
_Wechat_Token = None
_Token_Url = getattr(Config, 'TOKEN_URL', None)
_Corp_ID = getattr(Config, "CORP_ID", None)
_Secret = getattr(Config, "SECRET", None)
_Push_Url = getattr(Config, "PUSH_URL", None)
_Agent_ID = getattr(Config, "AGENT_ID", None)

_Session = requests.Session()


def send_email(title=u'Email Notification', content=None, receiver_list=None, create_at=None):
    try:
        if receiver_list is None:
            receiver_list = list()
        email_body = Email_Tmp_Top + Email_Tmp_Foot.format(create_at, content)
        message = MIMEText(email_body, "html", "utf-8")
        message['from'] = Header("AOPS<{}>".format(_EmailUserAccount), "utf-8")
        message['to'] = Header(",".join(receiver_list), "utf-8")
        message['subject'] = Header(title, "utf-8")
        smtp_ins = smtplib.SMTP_SSL()
        smtp_ins.connect(_EmailServer, _EmailServerPort)
        smtp_ins.login(_EmailUserAccount, _EmailUserPwd)
        smtp_ins.sendmail(_EmailUserAccount, receiver_list, message.as_string())
    except Exception as e:
        raise EmailFailedError('{}'.format(e))


def send_sms(phone_list=None, content='', send_time='', product_id=724, channel_id=0, need_report=1):
    try:
        phones = ','.join(phone_list)
        params = dict(
            userName=_SmsAccount,
            userPassword=_SmsPwd,
            content=content,
            phoneNums=phones,
            sendTime=send_time,
            productId=product_id,
            channelId=channel_id,
            needReport=need_report,
            type='sendMsg'
        )
        _Session.post(_SmsAPI, params=params)
    except Exception as e:
        raise SmsFailedError('{}'.format(e))


def send_wechat(receiver_list=None, message='test', count=0):
    global _Wechat_Token
    count += 1
    if count > 3:
        return
    try:
        if _Wechat_Token is None:
            token_url = _Token_Url.format(_Corp_ID, _Secret)
            resp_token = _Session.get(token_url).json()
            _Wechat_Token = resp_token["access_token"]
        receivers = '|'.join(receiver_list)
        msg_body = {
            "touser": receivers,
            "msgtype": "text",
            "agentid": _Agent_ID,
            "text": {
                "content": message
            },
            "safe": 0
        }
        push_url = _Push_Url.format(_Wechat_Token)
        resp_push = _Session.post(push_url, json=msg_body)
        errmsg = resp_push.json()['errmsg']

        if errmsg != 'ok':
            _Wechat_Token = None
            send_wechat(receiver_list=receiver_list, message=message, count=count)
            return
    except Exception as e:
        raise WechatFailedError('{}'.format(e))


if __name__ == '__main__':
    send_wechat(receiver_list=['bwang'])



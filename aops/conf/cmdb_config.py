#!/usr/bin/env python
# -*- coding:utf-8 -*-

CMDB_HTTP_SCHEMA = "http"
CMDB_HOST = "10.111.2.59"
CMDB_PORT = 8083
SUPPLIER_ACCOUNT = 0
CMDB_VERSION = 'v3'
CMDB_BUSINESSES = {
    'LDDS': 'vm_private',
    'CLOUD': 'vm_public',
    'OTHER': 'OTHER'
}

LDDS_HOST_KEYNAME_MAP={   # LDDS 主机
    'bk_inst_id': u'实例ID',
    'site': u'机房',
    'cabinet': u'机柜',
    'bk_inst_name': u'实例名',
    'status': u'状态',
    'os': u'操作系统',
    'host': u'宿主机',
    'downstream_ip': u'下游IP',
    'monitor_ip': u'监控IP',
    'upstream_ip1': u'上游IP1',
    'upstream_ip2': u'上游IP2',
    'cwdm_ip1': u'内网IP1',
    'cwdm_ip2': u'内网IP2',
    'app': u'应用',
    'metadata': u'元数据',
    'other_ip': u'其他IP',
    'ansible_fact': u'系统信息'
}

CLOUD_HOST_KEYNAME_MAP={    # 云平台主机
    'bk_inst_id': u'实例ID',
    'site': u'机房',
    'cabinet': u'机柜',
    'bk_inst_name': u'实例名',
    'lan_ip': '',
    'status': u'状态',
    'host': u'宿主机',
    'metadata': u'元数据',
    'os': u'操作系统',
    'special_ip': u'专线IP',
    'other_ip': u'其他IP',
    'wan_ip': u'外网IP',
    'audit_ip': u'审计IP',
    'nettype': u'网络类型',
    'qs': '券商',
    'xxs': '信息商',
    'sseinfo': u'信息公司',
    'app': '应用',
    'credit': u'证书',
    'tenant': u'租户',
    'szwg_ip': u'深圳网管IP',
    'public_ldds_ip': u'云平台LDDSIP',
    'zf_ip': u'转发IP',
    'ldds_ip': u'LDDSIP',
    'ansible_fact': u'系统信息'
}

BUSINESS_HOST_KEYNAME_MAP = {
    'LDDS': LDDS_HOST_KEYNAME_MAP,
    'CLOUD': CLOUD_HOST_KEYNAME_MAP
}
LDDS_HOST_KEY_MAP = {
    'bk_inst_name': 'name',
    'os': 'os',
    'site': 'site',
    'cabinet': 'cabinet',
    'host': 'machine',
    'cwdm_ip1': 'identity_ip'
    # other keys will be stored into host.others
}

CLOUD_HOST_KEY_MAP = {
    'bk_inst_name': 'name',
    'os': 'os',
    'site': 'site',
    'cabinet': 'cabinet',
    'host': 'machine',
    'lan_ip': 'identity_ip'
}

BUSINESS_HOST_KEY_MAP = {
    'LDDS': LDDS_HOST_KEY_MAP,
    'CLOUD': CLOUD_HOST_KEY_MAP
}

HOST_ACCOUNT_KEY_MAP = {
    'Account': 'username',
    'IPAddress': 'ip',
    'Hostname': 'host_name',
    'Password': 'password'
}

MACHINE_KEYNAME_MAP = {    # 物理机
    'bk_host_id': u'主机ID',
    'vendor': u'供应商',
    'brand': u'品牌',
    'bk_host_innerip': u'内网IP',
    'ipmi_ip': u'IPMI',
    'bk_host_outerip': u'外网IP',
    'bk_asset_id': u'固资编号',
    'bk_sn': u'设备SN',
    'bk_comment': u'备注',
    'bk_host_name': u'主机名称',
    'bk_service_term': u'质保年限'
}

APP_KEYNAME_MAP = {
    "type": u"类型",    # 应用类型 1：转发， 2：发布， 3：中间件， 4：数据库
    "status": u"状态",  # 应用状态 1： 上线 2： 下线， 3：测试
    "bk_inst_name": u"实例名", # test_for_aops
    "memo": u"备注",
    "dependence": u"外部依赖",
    "cn_inst_name": u"中文实例名",
    "market": u"市场",
    "package": u"程序",
    "version": u"版本",
    "conf": u"配置文件",
    "package_location": u"软件包位置"
}

APP_KEY_MAP = {
    "type": "type",    # 应用类型 1：转发， 2：发布， 3：中间件， 4：数据库
    "status": "instance_status",  # 应用状态 1： 上线 2： 下线， 3：测试
    "bk_inst_name": "instance_name", # test_for_aops
    "memo": "",
    "dependence": "",
    "cn_inst_name": "",
    "market": "",
    "package": "",
    "version": "version",
    "conf": "cfg_file_repository",
    "package_location": "sw_package_repository"
}

APP_STATUS = [0, 1, 2, 3]  # 0: new , 1: modified, 2: published, 3: offline
APP_LANGUAGES = ['JAVA', 'C', 'GO', 'SHELL']

# -*- coding: utf-8 -*-
"""

新建配置文件 cloudflare.ini (与本文件同目录):

[cloudflare]
token = api_token
zone_id = zone_id
# 需要更新的动态域名
record_name = domain.com
# 需要排除的IP,多个用逗号分隔
exclude_ips = 6.6.6.6

"""

import datetime
import http.client
import requests
import json
import sys
import os
import re
from configparser import ConfigParser
from urllib.parse import quote

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "cloudflare.ini")


def load_config(path=CONFIG_PATH):
    config = ConfigParser()
    if not config.read(path, encoding='utf-8'):
        raise FileNotFoundError(f"未找到配置文件: {path}，请参考本文件顶部说明创建")

    section = config['cloudflare']
    exclude_ips = [ip.strip() for ip in section.get('exclude_ips', '').split(',') if ip.strip()]

    return {
        'token': section.get('token'),
        'zone_id': section.get('zone_id'),
        'record_name': section.get('record_name'),
        'exclude_ips': exclude_ips,
    }


_cfg = load_config()

# 云解析配置
CF_Zone_ID = _cfg['zone_id']
# 需要更新的动态域名
CF_Record_Name = _cfg['record_name']
# 需要排除的IP
Exclude_IPs = _cfg['exclude_ips']

CF_Headers = {
    'Authorization': 'Bearer ' + _cfg['token'],
}

# 网络请求超时时间(秒)，避免网络异常时脚本无限期卡死
REQUEST_TIMEOUT = 15


def dns_list():
    conn = http.client.HTTPSConnection("api.cloudflare.com", timeout=REQUEST_TIMEOUT)
    try:
        conn.request("GET", f"/client/v4/zones/{CF_Zone_ID}/dns_records", headers=CF_Headers)
        res = conn.getresponse()
        data = res.read()
        return json.loads(data.decode("utf-8"))
    finally:
        conn.close()


# identifier: record id
def dns_detail(record_name):
    conn = http.client.HTTPSConnection("api.cloudflare.com", timeout=REQUEST_TIMEOUT)
    try:
        conn.request("GET", f"/client/v4/zones/{CF_Zone_ID}/dns_records?name.exact={quote(record_name)}", headers=CF_Headers)
        res = conn.getresponse()
        data = res.read()
        return json.loads(data.decode("utf-8"))
    finally:
        conn.close()


# identifier: record id
def dns_update(identifier, name, IP):
    conn = http.client.HTTPSConnection("api.cloudflare.com", timeout=REQUEST_TIMEOUT)
    try:
        payload = {
            "type": "A",
            "name": name,
            "content": IP,
            "ttl": 1,
        }
        conn.request("PUT", f"/client/v4/zones/{CF_Zone_ID}/dns_records/{identifier}", json.dumps(payload), CF_Headers)
        res = conn.getresponse()
        data = res.read()
        return json.loads(data.decode("utf-8"))
    finally:
        conn.close()


def dns_patch(identifier, IP):
    conn = http.client.HTTPSConnection("api.cloudflare.com", timeout=REQUEST_TIMEOUT)
    try:
        payload = {
            "content": IP,
            "ttl": 120,  # 非 auto(1) 的 ttl, 需要设置 proxied 为 False
            "proxied": False,
        }
        conn.request("PATCH", f"/client/v4/zones/{CF_Zone_ID}/dns_records/{identifier}", json.dumps(payload), CF_Headers)
        res = conn.getresponse()
        data = res.read()
        return json.loads(data.decode("utf-8"))
    finally:
        conn.close()


def get_my_global_ip():
    query_sites = ["http://myip.ipip.net", "http://ipv4.icanhazip.com/", "http://ip.42.pl/raw"]
    result = None
    for site in query_sites:
        try:
            result = requests.get(site, timeout=REQUEST_TIMEOUT)
            break
        except requests.RequestException:
            continue
    if result is not None and result.status_code == 200:
        ip = re.findall(r'[0-9]+(?:\.[0-9]+){3}', result.text)
        if ip:
            return ip[0]
    return "0.0.0.0"


def initlog():
    # 按月拆分日志文件，如 dns-202608.log，文件不存在时会自动创建
    log_name = datetime.datetime.now().strftime("dns-%Y%m.log")
    filepath = os.path.join(os.path.dirname(__file__), log_name)
    sys.stderr = open(filepath, 'a', encoding="utf-8")


def log(status, message):
    """按 [时间] 状态 说明 的格式输出一行日志，status 用于一眼看出是否出问题"""
    nowtime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{nowtime}] {status:<5} {message}", file=sys.stderr, flush=True)


def cf_error_message(resp):
    """从 Cloudflare 返回结果中提取简洁的错误说明"""
    errors = resp.get('errors') or []
    if errors:
        return "; ".join(e.get('message', str(e)) for e in errors)
    return str(resp)


def main():

    initlog()

    my_ip = get_my_global_ip()
    if my_ip == "0.0.0.0" or my_ip in Exclude_IPs:
        log("ERROR", "获取本机公网IP失败或命中排除列表")
        return

    # 测试: 获取DNS记录列表
    # all_records = dns_list()
    # print(all_records)

    detail = dns_detail(CF_Record_Name)
    if not detail['success']:
        log("ERROR", f"查询DNS记录失败: {cf_error_message(detail)}")
        return

    result = detail["result"][0]
    current_cf_ip = result['content']
    record_id = result['id']

    if current_cf_ip == my_ip:
        log("OK", f"IP未变化 ({my_ip})，无需更新")
        return

    resp = dns_update(record_id, CF_Record_Name, my_ip)
    if not resp['success']:
        log("ERROR", f"更新DNS记录失败 ({current_cf_ip} → {my_ip}): {cf_error_message(resp)}")
        return

    log("OK", f"IP已更新: {current_cf_ip} → {my_ip}")


if __name__ == '__main__':
    main()

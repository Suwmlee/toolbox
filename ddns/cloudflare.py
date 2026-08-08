
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
import requests
import sys
import os
import re
import traceback
from configparser import ConfigParser

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

CF_API_BASE = "https://api.cloudflare.com/client/v4"

# 网络请求超时时间(秒)，避免网络异常时脚本无限期卡死
REQUEST_TIMEOUT = 15

# 复用同一个 Session(及其底层连接)，减少重复的 TCP/TLS 握手
_session = requests.Session()
_session.headers.update({'Authorization': 'Bearer ' + _cfg['token']})


def dns_list():
    resp = _session.get(f"{CF_API_BASE}/zones/{CF_Zone_ID}/dns_records", timeout=REQUEST_TIMEOUT)
    return resp.json()


# identifier: record id
def dns_detail(record_name):
    resp = _session.get(
        f"{CF_API_BASE}/zones/{CF_Zone_ID}/dns_records",
        params={"name.exact": record_name},
        timeout=REQUEST_TIMEOUT,
    )
    return resp.json()


# identifier: record id
def dns_update(identifier, name, IP):
    payload = {
        "type": "A",
        "name": name,
        "content": IP,
        "ttl": 1,
    }
    resp = _session.put(
        f"{CF_API_BASE}/zones/{CF_Zone_ID}/dns_records/{identifier}",
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )
    return resp.json()


def dns_patch(identifier, IP):
    payload = {
        "content": IP,
        "ttl": 120,  # 非 auto(1) 的 ttl, 需要设置 proxied 为 False
        "proxied": False,
    }
    resp = _session.patch(
        f"{CF_API_BASE}/zones/{CF_Zone_ID}/dns_records/{identifier}",
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )
    return resp.json()


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

    try:
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
    except requests.RequestException as e:
        log("ERROR", f"网络请求异常: {e}")
    except Exception:
        log("ERROR", f"未预期的异常:\n{traceback.format_exc()}")


if __name__ == '__main__':
    main()

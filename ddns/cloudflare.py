
# -*- coding: utf-8 -*-
"""

新建配置文件 cloudflare.ini (与本文件同目录):

[cloudflare]
email = your@gmail.com
token = api_token
api_key = global_api_key
zone_id = zone_id
# 需要更新的动态域名
record_name = link.com
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

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "cloudflare.ini")


def load_config(path=CONFIG_PATH):
    config = ConfigParser()
    if not config.read(path, encoding='utf-8'):
        raise FileNotFoundError(f"未找到配置文件: {path}，请参考本文件顶部说明创建")

    section = config['cloudflare']
    exclude_ips = [ip.strip() for ip in section.get('exclude_ips', '').split(',') if ip.strip()]

    return {
        'email': section.get('email'),
        'token': section.get('token'),
        'api_key': section.get('api_key'),
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
exclude_ips = _cfg['exclude_ips']

headers = {
    'Content-Type': "application/json",
    'X-Auth-Email': _cfg['email'],
    'X-Auth-Key': _cfg['api_key'],
    'Authorization': 'Bearer ' + _cfg['token'],
}


def dns_list():
    conn = http.client.HTTPSConnection("api.cloudflare.com")
    conn.request("GET", f"/client/v4/zones/{CF_Zone_ID}/dns_records", headers=headers)
    res = conn.getresponse()
    data = res.read()
    return json.loads(data.decode("utf-8"))


# identifier: record id
def dns_detail(record_name):
    conn = http.client.HTTPSConnection("api.cloudflare.com")
    conn.request("GET", f"/client/v4/zones/{CF_Zone_ID}/dns_records?name={record_name}", headers=headers)
    res = conn.getresponse()
    data = res.read()
    return json.loads(data.decode("utf-8"))


# identifier: record id
def dns_update(identifier, name, IP):
    conn = http.client.HTTPSConnection("api.cloudflare.com")
    payload = {
        "type": "A",
        "name": name,
        "content": IP,
        "ttl": 1,
    }
    conn.request("PUT", f"/client/v4/zones/{CF_Zone_ID}/dns_records/{identifier}", json.dumps(payload), headers)
    res = conn.getresponse()
    data = res.read()
    return json.loads(data.decode("utf-8"))


def dns_patch(identifier, IP):
    conn = http.client.HTTPSConnection("api.cloudflare.com")
    payload = {
        "content": IP,
        "ttl": 120,  # 非 auto(1) 的 ttl, 需要设置 proxied 为 False
        "proxied": False,
    }
    conn.request("PATCH", f"/client/v4/zones/{CF_Zone_ID}/dns_records/{identifier}", json.dumps(payload), headers)
    res = conn.getresponse()
    data = res.read()
    return json.loads(data.decode("utf-8"))


def get_my_global_ip():
    query_sites = ["http://myip.ipip.net", "http://ipv4.icanhazip.com/", "http://ip.42.pl/raw"]
    for site in query_sites:
        try:
            result = requests.get(site, timeout=15)
            break
        except:
            continue
    if result.status_code == 200:
        ip = re.findall( r'[0-9]+(?:\.[0-9]+){3}', result.text)
        return ip[0]
    else:
        return "0.0.0.0"


def initlog():
    filepath = os.path.join(os.path.dirname(__file__), "ddns.log")
    sys.stderr = open(filepath, 'a', encoding="utf-8")


def main():

    initlog()
    nowtime = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    print(nowtime + " 开始检测DDNS...", file=sys.stderr, flush=True)

    # 需要更新的动态域名
    record_name = CF_Record_Name

    my_ip = get_my_global_ip()
    if my_ip == "0.0.0.0" or my_ip in exclude_ips:
        print("  获取 WAN IP 异常", file=sys.stderr, flush=True)
        return
    detail = dns_detail(record_name)
    if not detail['success']:
        print(detail, file=sys.stderr, flush=True)
        return
    result = detail["result"][0]
    current_cf_ip = result['content']
    record_id = result['id']

    if current_cf_ip != my_ip:
        print(f"  检测变动: 当前CF记录IP: {current_cf_ip} 本地实际IP: {my_ip}", file=sys.stderr, flush=True)
        resp = dns_update(record_id, record_name, my_ip)

        if not resp['success']:
            print(resp, file=sys.stderr, flush=True)
            return
        else:
            # notify this change
            print("  更新完成", file=sys.stderr, flush=True)


if __name__ == '__main__':
    main()

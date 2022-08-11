# -*- coding: utf-8 -*-
"""

新建配置文件 config.ini :

[telegram bot name]
chat_id =
token =

[proxy]
#address = socks5h://127.0.0.1:1080
address =

[site A]
url = https://aaaaaa/userdetails.php?id=10000
cookies = <full cookies string>
regex = <regex rule>

[site B]
url = https://bbbbbb/userdetails.php?id=10000
cookies = <full cookies string>
useproxy = True

"""

import requests
import datetime
import os
from configparser import ConfigParser
from lxml import etree
from http.cookies import SimpleCookie


def request(url, cookies, proxyaddress):
    """ 封装请求
    """
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3100.0 Safari/537.36"}
    timeout = 20
    
    if proxyaddress and proxyaddress != '':
        http_proxy = proxyaddress
        https_proxy = proxyaddress
        proxydict = {
            "http": http_proxy,
            "https": https_proxy
        }
        result = requests.get(str(url), headers=headers, cookies=cookies, proxies=proxydict, timeout=timeout)
    else:
        result = requests.get(str(url), headers=headers, cookies=cookies, timeout=timeout)
    return result


def sendmessage(bottoken, chat_id, message: str, proxyaddress):
    """ 使用telegram bot发送结果
    """
    url = "https://api.telegram.org/bot"+bottoken+"/sendMessage?chat_id="+chat_id+"&text="+message
    for i in range(3):
        try:
            result = request(url, None, proxyaddress)
            if result.status_code == 200:
                break
        except:
            pass


def login(url: str, rawcookie, regex, proxyaddress = None):
    """ 登录网站返回最近动向
    """
    try:
        cookie = SimpleCookie()
        cookie.load(rawcookie)
        cookies = {}
        for key, morsel in cookie.items():
            cookies[key] = morsel.value

        for i in range(3):
            try:
                updatestatus = None
                result = request(url, cookies, proxyaddress)

                if result.status_code == 200:
                    updatestatus = parse(result.text, regex)
                    if updatestatus:
                        break
            except Exception as e:
                updatestatus = str(e)

        if not updatestatus:
            updatestatus = str(result.status_code) + ' : ' + result.reason
    except Exception as e:
        updatestatus = str(e)
    return updatestatus


def parse(content, regex):
    """ 解析最近动向
    """
    try:
        html = etree.fromstring(content, etree.HTMLParser())
        if regex == "":
            result = html.xpath('//td[contains(text(), "最近動向") or contains(text(), "最近动向")]/following-sibling::td[1]')
        else:
            result = html.xpath(regex)
        for row in result:
            info = row.xpath('string(.)')
            if info:
                info = str(info).replace('\n', '').replace('\r', '')
                info = " ".join(info.split())
                return info
        return None
    except:
        return None


def savelog(content: str):
    filepath = os.path.join(os.path.dirname(__file__), "autocheck.log")
    with open(filepath, 'a', encoding="utf-8") as file:
        file.write(content)


def main():

    config = ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), "config.ini"), encoding='utf-8')

    bottoken = ''
    chat_id = ''
    websits = []
    proxyaddress = ''
    for configsection in config:
        if (
            "chat_id" in config[configsection]
            and "token" in config[configsection]
        ):
            chat_id = config[configsection]["chat_id"]
            bottoken = config[configsection]["token"]
        elif (
            "url" in config[configsection]
            and "cookies" in config[configsection]
        ):
            siteurl = config[configsection]["url"]
            sitecookie = config[configsection]["cookies"]
            if 'regex' in config[configsection] and config[configsection]["regex"]:
                regex = config[configsection]["regex"]
            else:
                regex = ""
            if 'useproxy' in config[configsection] and config[configsection]["useproxy"]:
                useproxy = True
            else:
                useproxy = False
            if sitecookie != '' and siteurl != '':
                websits.append((configsection, siteurl, sitecookie, regex, useproxy))
        elif "address" in config[configsection]:
            proxyaddress = config[configsection]["address"]
        elif configsection == "DEFAULT":
            continue

    nowtime = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    message = nowtime + '刷新站点:' + '\r\n'
    for sitename, siteurl, sitecookie, regex, useproxy in websits:
        if useproxy:
            updateinfo = login(siteurl, sitecookie, regex, proxyaddress)
        else:
            updateinfo = login(siteurl, sitecookie, regex)
        try:
            message += sitename.ljust(15) + " 最近动向:  " + updateinfo + ' \r\n'
        except:
            pass

    savelog(message)
    if bottoken != '' and chat_id != '':
        sendmessage(bottoken, chat_id, message, proxyaddress)


if __name__ == "__main__":

    main()


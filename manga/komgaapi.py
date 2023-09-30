
import requests
import json

from http.cookies import SimpleCookie


class KomgaApi():

    def __init__(self, domain, rawcookie):
        self.domain = domain

        cookie = SimpleCookie()
        cookie.load(rawcookie)
        self.cookies = {}
        for key, morsel in cookie.items():
            self.cookies[key] = morsel.value
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"}

    def get_library(self):
        """ 获取本子库
        http://localhost:25600/api/v1/libraries
        """
        url = '{0}/api/v1/libraries'.format(self.domain)
        response = requests.get(url, headers=self.headers, cookies=self.cookies)
        result = json.loads(response.content)
        return result

    def get_library_series(self, lid):
        """ 获取指定库内的系列
        """
        url = '{0}/api/v1/series?library_id={1}&size=50'.format(self.domain, lid)
        response = requests.get(url, headers=self.headers, cookies=self.cookies)
        series = []
        result = json.loads(response.content)
        pages = result['totalPages']
        for ct in result['content']:
            series.append(ct)
        if pages > 1:
            for i in range(1, pages):
                url = '{0}/api/v1/series?library_id={1}&size=50&page={2}'.format(self.domain, lid, i)
                response = requests.get(url, headers=self.headers, cookies=self.cookies)
                result = json.loads(response.content)
                for ct in result['content']:
                    series.append(ct)

        return series

    def get_series_book(self, sid):
        """ 获取系列内本子
        http://localhost:25600/api/v1/series/0CWPH5WHP6W28/books
        """
        url = '{0}/api/v1/series/{1}/books?size=50'.format(self.domain, sid)
        response = requests.get(url, headers=self.headers, cookies=self.cookies)
        books = []
        result = json.loads(response.content)
        pages = result['totalPages']
        for cb in result['content']:
            books.append(cb)
        if pages > 1:
            for i in range(1, pages):
                url = '{0}/api/v1/series/{1}/books?size=50&page={2}'.format(self.domain, sid, i)
                response = requests.get(url, headers=self.headers, cookies=self.cookies)
                result = json.loads(response.content)
                for cb in result['content']:
                    books.append(cb)

        return books

    def update_series_meta(self, id, payload):
        """ 更新系列元数据
        系列元数据没有 writer 只能考虑 tag
        """
        url = '{0}/api/v1/series/{1}/metadata'.format(self.domain, id)
        requests.patch(url, json.dumps(payload), headers=self.headers, cookies=self.cookies)

    def update_book_meta(self, id, payload):
        """ 更新本子元数据
        """
        url = '{0}/api/v1/books/{1}/metadata'.format(self.domain, id)
        headers={'content-type': 'application/json'}
        result = requests.patch(url, data=json.dumps(payload), headers=headers, cookies=self.cookies)
        if result.status_code == 204:
            return True
        return False

    def scan_lib(self, lid):
        """ 扫描 komga 库
        http://localhost:25600/api/v1/libraries/xxx/scan?deep=false
        """
        url = '{0}/api/v1/libraries/{1}/scan?deep=false'.format(self.domain, lid)
        requests.post(url, headers=self.headers, cookies=self.cookies)

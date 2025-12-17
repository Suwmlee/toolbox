# -*- coding: utf-8 -*-
"""
Komga API封装
"""
import json
import requests
from http.cookies import SimpleCookie
from typing import List, Dict, Optional


class KomgaApi:
    """Komga API客户端"""
    
    def __init__(self, domain: str, raw_cookie: str):
        """
        初始化API客户端
        
        Args:
            domain: Komga服务域名
            raw_cookie: Cookie字符串
        """
        self.domain = domain
        
        # 解析Cookie
        cookie = SimpleCookie()
        cookie.load(raw_cookie)
        self.cookies = {key: morsel.value for key, morsel in cookie.items()}
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/104.0.0.0 Safari/537.36"
        }
    
    def get_libraries(self) -> List[Dict]:
        """
        获取所有漫画库
        
        Returns:
            漫画库列表
        """
        url = f'{self.domain}/api/v1/libraries'
        response = requests.get(url, headers=self.headers, cookies=self.cookies)
        return json.loads(response.content)
    
    def get_library_series(self, library_id: str, page_size: int = 50) -> List[Dict]:
        """
        获取指定库内的系列
        
        Args:
            library_id: 库ID
            page_size: 每页数量
            
        Returns:
            系列列表
        """
        url = f'{self.domain}/api/v1/series?library_id={library_id}&size={page_size}'
        response = requests.get(url, headers=self.headers, cookies=self.cookies)
        result = json.loads(response.content)
        
        series = list(result.get('content', []))
        total_pages = result.get('totalPages', 1)
        
        # 分页获取
        for page in range(1, total_pages):
            url = f'{self.domain}/api/v1/series?library_id={library_id}&size={page_size}&page={page}'
            response = requests.get(url, headers=self.headers, cookies=self.cookies)
            result = json.loads(response.content)
            series.extend(result.get('content', []))
        
        return series
    
    def get_series_books(self, series_id: str, page_size: int = 50) -> List[Dict]:
        """
        获取系列内的所有本子
        
        Args:
            series_id: 系列ID
            page_size: 每页数量
            
        Returns:
            本子列表
        """
        url = f'{self.domain}/api/v1/series/{series_id}/books?size={page_size}'
        response = requests.get(url, headers=self.headers, cookies=self.cookies)
        result = json.loads(response.content)
        
        books = list(result.get('content', []))
        total_pages = result.get('totalPages', 1)
        
        # 分页获取
        for page in range(1, total_pages):
            url = f'{self.domain}/api/v1/series/{series_id}/books?size={page_size}&page={page}'
            response = requests.get(url, headers=self.headers, cookies=self.cookies)
            result = json.loads(response.content)
            books.extend(result.get('content', []))
        
        return books
    
    def update_series_metadata(self, series_id: str, payload: Dict) -> bool:
        """
        更新系列元数据
        
        Args:
            series_id: 系列ID
            payload: 元数据
            
        Returns:
            是否成功
        """
        url = f'{self.domain}/api/v1/series/{series_id}/metadata'
        response = requests.patch(
            url, 
            json.dumps(payload), 
            headers=self.headers, 
            cookies=self.cookies
        )
        return response.status_code == 204
    
    def update_book_metadata(self, book_id: str, payload: Dict) -> bool:
        """
        更新本子元数据
        
        Args:
            book_id: 本子ID
            payload: 元数据
            
        Returns:
            是否成功
        """
        url = f'{self.domain}/api/v1/books/{book_id}/metadata'
        headers = {'content-type': 'application/json'}
        headers.update(self.headers)
        
        response = requests.patch(
            url, 
            data=json.dumps(payload), 
            headers=headers, 
            cookies=self.cookies
        )
        return response.status_code == 204
    
    def scan_library(self, library_id: str, deep: bool = False):
        """
        扫描指定库
        
        Args:
            library_id: 库ID
            deep: 是否深度扫描
        """
        url = f'{self.domain}/api/v1/libraries/{library_id}/scan?deep={str(deep).lower()}'
        requests.post(url, headers=self.headers, cookies=self.cookies)


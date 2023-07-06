
import requests


class KomgaApi():

    def __init__(self, cookies):
        cookies = cookies


    def get_series(self):
        """ 获取系列数据
        http://localhost:25600/api/v1/series
        系列内有 url 参数（好像就是文件地址）可以从这里判定所属的具体 library
        """
        print("get series")


    def update_series_meta(self, id):
        """ 更新系列元数据
        系列元数据没有 writer 只能考虑 tag
        http://localhost:25600/api/v1/series/0CWPH5WHP6W28/metadata
        """
        print("元数据")


    def get_series_book(self, id):
        """ 获取系列内本子
        http://localhost:25600/api/v1/series/0CWPH5WHP6W28/books
        """
        print("获取系列内本子")


    def update_book_meta(self, id):
        """ 更新本子元数据
        http://localhost:25600/api/v1/books/0CWPH5WS66QNE/metadata
        """
        print("更新本子元数据")



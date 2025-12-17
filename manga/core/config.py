# -*- coding: utf-8 -*-
"""
配置管理模块
"""
import os
from yaml import load


class Config:
    """配置管理类"""
    
    def __init__(self, config_path: str = ""):
        try:
            from yaml import CLoader as Loader
        except ImportError:
            from yaml import Loader
        
        if not config_path:
            local_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(local_path, 'manga.yaml')
        
        with open(config_path, mode="r", encoding="utf8") as f:
            self._config = load(f.read(), Loader=Loader)
        
        self._debug = self._config.get('debug', True)
    
    @property
    def debug(self) -> bool:
        """是否为调试模式（True=不实际执行，False=正式执行）"""
        return self._debug
    
    @debug.setter
    def debug(self, value: bool):
        """设置调试模式"""
        self._debug = value
    
    @property
    def manga_types(self) -> list:
        """支持的漫画文件类型"""
        return self._config.get('manga-type', ['.zip', '.cbz', '.pdf'])
    
    @property
    def tachiyomi(self) -> dict:
        """Tachiyomi配置"""
        return self._config.get('tachiyomi', {})
    
    @property
    def organize_manga(self) -> dict:
        """整理漫画配置"""
        return self._config.get('organize-manga', {})
    
    @property
    def komga_lib(self) -> dict:
        """Komga库配置"""
        return self._config.get('komgalib', {})
    
    @property
    def groups(self) -> list:
        """需要移除的组名"""
        return self._config.get('groups', [])
    
    @property
    def tags(self) -> list:
        """标签配置"""
        return self._config.get('tags', [])
    
    def get(self, key: str, default=None):
        """获取配置项"""
        return self._config.get(key, default)


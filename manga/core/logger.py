# -*- coding: utf-8 -*-
"""
日志模块
"""
import logging
import sys


class Logger:
    """日志管理类"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._logger = logging.getLogger('manga')
        self._logger.setLevel(logging.INFO)
        
        # 控制台输出
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        
        # 格式化
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        self._logger.addHandler(handler)
    
    @property
    def logger(self):
        return self._logger
    
    def info(self, msg: str):
        """信息日志"""
        self._logger.info(msg)
    
    def warning(self, msg: str):
        """警告日志"""
        self._logger.warning(msg)
    
    def error(self, msg: str):
        """错误日志"""
        self._logger.error(msg)
    
    def debug(self, msg: str):
        """调试日志"""
        self._logger.debug(msg)


# 全局日志实例
logger = Logger()


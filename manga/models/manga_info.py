# -*- coding: utf-8 -*-
"""
漫画信息模型
"""
import os
from typing import List, Optional


class MangaInfo:
    """漫画信息类"""
    
    def __init__(self, root: str):
        """
        初始化漫画信息
        
        Args:
            root: 漫画目录路径
        """
        self.full_path = root
        self.name = os.path.basename(root)
        self.chapters: List[str] = []
        self.is_manga = True
        self.is_tankobon = False
        self.is_series = False
        
        # 扩展属性
        self.type_name: Optional[str] = None
        self.ended = False
        self.keep_tag = True
        self.dst_folder = ''
    
    def set_chapters(self, chapters: List[str]):
        """设置章节列表"""
        self.chapters = chapters
        if len(chapters) < 1:
            self.is_manga = False
        else:
            self._detect_manga_type()
    
    def _detect_manga_type(self):
        """检测漫画类型（单本/系列）"""
        from core.constants import SINGLE_CHAPTER_NAMES
        
        if len(self.chapters) < 2:
            if self.chapters[0] in SINGLE_CHAPTER_NAMES:
                self.is_tankobon = True
                self.is_series = False
            else:
                # 可能是单本，目前只有一个章节
                self.is_tankobon = True
                self.is_series = False
        else:
            self.is_tankobon = False
            self.is_series = True
    
    def analyze_type(self, config: dict):
        """
        分析漫画类型
        
        Args:
            config: 过滤器配置
        """
        for filter_item in config.get('filters', []):
            # 检查完结列表
            if 'ended' in filter_item and self.name in filter_item['ended']:
                self.ended = True
                self.type_name = filter_item['name']
                break
            
            # 根据类型匹配
            filter_type = filter_item.get('type')
            
            if filter_type == 'name':
                if self.name in filter_item.get('names', []):
                    self.type_name = filter_item['name']
                    
            elif filter_type == 'folder':
                for folder in filter_item.get('folders', []):
                    if self.full_path.startswith(folder):
                        self.type_name = filter_item['name']
                        break
                        
            elif filter_type == 'tankobon':
                if self.is_tankobon:
                    self.type_name = filter_item['name']
                    
            elif filter_type == 'series':
                if self.is_series:
                    self.type_name = filter_item['name']
            
            if self.type_name:
                break
    
    def query_mapping(self, config: dict):
        """
        查询漫画映射规则
        
        Args:
            config: 映射配置
        """
        for mapping in config.get('mapping', []):
            if mapping['name'] == self.type_name:
                flag = mapping['ended'] if self.ended else mapping['default']
                
                if flag == 'move':
                    self.dst_folder = mapping.get('dst', '')
                    self.keep_tag = False
                break
    
    def __repr__(self):
        return (f"MangaInfo(name={self.name}, chapters={len(self.chapters)}, "
                f"type={self.type_name}, tankobon={self.is_tankobon})")


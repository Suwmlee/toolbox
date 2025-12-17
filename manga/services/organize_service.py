# -*- coding: utf-8 -*-
"""
漫画整理服务
"""
import os
from core.config import Config
from core.logger import logger
from utils.file_utils import find_all_matches, get_folder_depth
from services.manga_service import MangaService


class OrganizeService:
    """漫画整理服务"""
    
    def __init__(self, config: Config):
        """
        初始化服务
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.manga_service = MangaService(config)
    
    def organize_manga(self):
        """执行漫画整理"""
        organize_config = self.config.organize_manga
        folders = organize_config.get('folders', [])
        
        for folder in folders:
            if not os.path.exists(folder):
                logger.error(f"目录不存在: {folder}")
                continue
            
            self._process_organize_folder(folder)
    
    def _process_organize_folder(self, folder: str):
        """
        处理整理文件夹
        
        Args:
            folder: 文件夹路径
        """
        logger.info(f"开始整理目录: {folder}")
        
        dirs = find_all_matches(folder)
        
        for entry in dirs:
            full_path = os.path.join(folder, entry)
            depth = get_folder_depth(full_path)
            
            if depth == 1:
                logger.info(f"处理一级目录: {full_path}")
                self._organize_single_manga(full_path, folder)
                
            elif depth == 2:
                logger.info(f"处理二级目录（可能包含作者层级）: {full_path}")
                sub_entries = os.listdir(full_path)
                
                for sub_entry in sub_entries:
                    sub_path = os.path.join(full_path, sub_entry)
                    logger.info(f"处理子目录: {sub_entry}")
                    self._organize_single_manga(sub_path, full_path)
            else:
                logger.warning(f"目录层级过深: {full_path}")
    
    def _organize_single_manga(self, manga_path: str, dst_folder: str):
        """
        整理单个漫画
        
        Args:
            manga_path: 漫画路径
            dst_folder: 目标文件夹
        """
        # 创建漫画信息
        manga_info = self.manga_service.create_manga_info(manga_path)
        if not manga_info:
            logger.warning("非漫画，跳过\n")
            return
        
        manga_info.dst_folder = dst_folder
        
        # 生成路径映射
        path_mapping = self.manga_service.fix_manga_chapters(
            manga_info,
            self.config.groups,
            self.config.tags,
            dst_folder
        )
        
        if not path_mapping:
            logger.warning("没有需要处理的文件，跳过\n")
            return
        
        # 处理文件
        self.manga_service.process_manga_files(
            path_mapping,
            self.config.debug
        )
        
        logger.info("整理完成！\n")


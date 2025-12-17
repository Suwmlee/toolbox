# -*- coding: utf-8 -*-
"""
Tachiyomi转移服务
"""
import os
from core.config import Config
from core.logger import logger
from utils.file_utils import find_all_matches
from services.manga_service import MangaService


class TransferService:
    """Tachiyomi转移服务"""
    
    def __init__(self, config: Config):
        """
        初始化服务
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.manga_service = MangaService(config)
    
    def transfer_manga(self):
        """执行Tachiyomi漫画转移"""
        tachiyomi_config = self.config.tachiyomi
        
        if not tachiyomi_config.get('enable', False):
            logger.warning("Tachiyomi功能未启用")
            return
        
        sources = tachiyomi_config.get('sources', [])
        
        for source in sources:
            if not os.path.exists(source):
                logger.error(f"源目录不存在: {source}")
                continue
            
            self._process_source_directory(source, tachiyomi_config)
    
    def _process_source_directory(self, source: str, tachiyomi_config: dict):
        """
        处理源目录
        
        Args:
            source: 源目录路径
            tachiyomi_config: Tachiyomi配置
        """
        logger.info(f"开始处理目录: {source}")
        
        dirs = find_all_matches(source)
        
        for entry in dirs:
            full_path = os.path.join(source, entry)
            self._process_manga(full_path, tachiyomi_config)
    
    def _process_manga(self, manga_path: str, tachiyomi_config: dict):
        """
        处理单个漫画
        
        Args:
            manga_path: 漫画路径
            tachiyomi_config: Tachiyomi配置
        """
        logger.info(f"分析漫画: {os.path.basename(manga_path)}")
        
        # 创建漫画信息
        manga_info = self.manga_service.create_manga_info(manga_path)
        if not manga_info:
            logger.warning("非漫画，跳过\n")
            return
        
        # 分析漫画类型
        self.manga_service.analyze_manga(manga_info, tachiyomi_config)
        
        # 检查是否需要移动
        if manga_info.keep_tag:
            logger.info("保持不动，跳过\n")
            return
        
        # 生成路径映射
        path_mapping = self.manga_service.fix_manga_chapters(
            manga_info,
            self.config.groups,
            self.config.tags,
            manga_info.dst_folder
        )
        
        if not path_mapping:
            logger.warning("没有需要处理的文件，跳过\n")
            return
        
        # 处理文件
        logger.info("开始处理文件...")
        self.manga_service.process_manga_files(
            path_mapping,
            self.config.debug
        )
        
        logger.info("处理完成！\n")


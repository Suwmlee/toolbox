# -*- coding: utf-8 -*-
"""
漫画处理服务
"""
import os
from typing import Dict, Optional
from ..core.config import Config
from ..core.logger import logger
from ..models.manga_info import MangaInfo
from ..utils.file_utils import find_manga_chapters, rename_file, zip_folder
from ..utils.name_utils import update_manga_name, update_chapter_name


class MangaService:
    """漫画处理服务"""
    
    def __init__(self, config: Config):
        """
        初始化服务
        
        Args:
            config: 配置对象
        """
        self.config = config
    
    def create_manga_info(self, root: str) -> Optional[MangaInfo]:
        """
        创建漫画信息对象
        
        Args:
            root: 漫画目录
            
        Returns:
            漫画信息对象，如果不是有效漫画则返回None
        """
        manga_info = MangaInfo(root)
        chapters = find_manga_chapters(root)
        manga_info.set_chapters(chapters)
        
        if not manga_info.is_manga:
            logger.warning(f"非漫画目录: {root}")
            return None
        
        return manga_info
    
    def analyze_manga(self, manga_info: MangaInfo, tachiyomi_config: dict):
        """
        分析漫画信息（用于tachiyomi转移）
        
        Args:
            manga_info: 漫画信息
            tachiyomi_config: Tachiyomi配置
        """
        manga_info.analyze_type(tachiyomi_config)
        manga_info.query_mapping(tachiyomi_config)
        
        logger.info(f"漫画类型: {manga_info.type_name}, 完结: {manga_info.ended}")
    
    def fix_manga_chapters(
        self, 
        manga_info: MangaInfo,
        groups: list,
        tags: list,
        dst_folder: str
    ) -> Dict[str, str]:
        """
        修复漫画章节名称和路径
        
        Args:
            manga_info: 漫画信息
            groups: 需要移除的组名
            tags: 标签列表
            dst_folder: 目标文件夹
            
        Returns:
            源路径到目标路径的映射字典
        """
        if manga_info.is_tankobon:
            return self._fix_tankobon(
                manga_info.full_path,
                manga_info.name,
                manga_info.chapters,
                groups,
                tags,
                dst_folder
            )
        else:
            return self._fix_series(
                manga_info.full_path,
                manga_info.name,
                manga_info.chapters,
                groups,
                tags,
                dst_folder
            )
    
    def _fix_tankobon(
        self,
        manga_folder: str,
        name: str,
        chapters: list,
        groups: list,
        bad_tags: list,
        dst_folder: str
    ) -> Dict[str, str]:
        """
        修复单本漫画
        
        Returns:
            {源路径: 目标路径}
        """
        result = {}
        manga_name = update_manga_name(name, groups, bad_tags)
        
        source_path = os.path.join(manga_folder, chapters[0])
        dest_path = os.path.join(dst_folder, manga_name, manga_name)
        
        logger.info(f"单本漫画: {chapters[0]} -> {manga_name}")
        result[source_path] = dest_path
        
        return result
    
    def _fix_series(
        self,
        manga_folder: str,
        name: str,
        chapters: list,
        groups: list,
        bad_tags: list,
        dst_folder: str
    ) -> Dict[str, str]:
        """
        修复系列漫画
        
        Returns:
            {源路径: 目标路径}
        """
        result = {}
        manga_name = update_manga_name(name, groups, bad_tags)
        
        for chapter in chapters:
            new_chapter = update_chapter_name(chapter)
            old_path = os.path.join(manga_folder, chapter)
            new_path = os.path.join(dst_folder, manga_name, new_chapter)
            result[old_path] = new_path
        
        return result
    
    def process_manga_files(self, path_mapping: Dict[str, str], dry_run: bool = True):
        """
        处理漫画文件（压缩和移动）
        
        Args:
            path_mapping: 路径映射字典
            dry_run: 是否为调试模式（True=不实际执行，False=正式执行）
        """
        for source, dest in path_mapping.items():
            self._process_single_file(source, dest, dry_run)
    
    def _process_single_file(self, source: str, dest: str, dry_run: bool):
        """处理单个文件"""
        # 检查是否已经是压缩文件
        is_compressed = False
        actual_source = source
        actual_dest = dest + '.zip'
        
        for zip_type in ['.zip', '.cbz', '.pdf', '.PDF']:
            if os.path.exists(source + zip_type):
                actual_source = source + zip_type
                actual_dest = dest + zip_type
                is_compressed = True
                break
        
        if actual_source == actual_dest:
            logger.debug(f"源和目标相同，跳过: {actual_source}")
            return
        
        if dry_run:
            logger.info(f"[调试模式] {actual_source} -> {actual_dest}")
            return
        
        if is_compressed:
            logger.info(f"直接移动压缩文件: {actual_source} -> {actual_dest}")
            rename_file(actual_source, actual_dest)
        else:
            logger.info(f"压缩并移动: {actual_source} -> {actual_dest}")
            zip_folder(actual_source, actual_dest)


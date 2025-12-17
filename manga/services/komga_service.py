# -*- coding: utf-8 -*-
"""
Komga服务
"""
import os
from core.config import Config
from core.logger import logger
from api.komga_api import KomgaApi
from utils.file_utils import rename_file, clean_empty_folders
from utils.name_utils import parse_tags_from_name


class KomgaService:
    """Komga整理服务"""
    
    def __init__(self, config: Config):
        """
        初始化服务
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.api: KomgaApi = None
    
    def organize_komga_manga(self):
        """执行Komga漫画整理"""
        lib_config = self.config.komga_lib
        
        if not lib_config.get('enable', False):
            logger.warning("Komga功能未启用")
            return
        
        domain = lib_config.get('domain')
        cookies = lib_config.get('cookies')
        
        if not domain or not cookies:
            logger.error("Komga配置不完整")
            return
        
        # 初始化API
        self.api = KomgaApi(domain, cookies)
        
        # 获取库列表
        libraries = self.api.get_libraries()
        
        if isinstance(libraries, dict) and libraries.get('error') == 'Unauthorized':
            logger.error("Komga认证失败")
            return
        
        # 处理每个库
        for library in libraries:
            self._process_library(library, lib_config)
        
        # 重新扫描所有库
        logger.info("开始重新扫描所有库...")
        for library in libraries:
            self.api.scan_library(library['id'])
        
        logger.info("Komga整理完成！")
    
    def _process_library(self, library: dict, lib_config: dict):
        """
        处理单个库
        
        Args:
            library: 库信息
            lib_config: 库配置
        """
        lib_name = library['name']
        lib_root = library['root']
        lib_names = lib_config.get('lib-names', [])
        
        if lib_name not in lib_names:
            return
        
        logger.info(f"处理库: {lib_name}")
        
        # 确定库等级
        tier3 = lib_config.get('Tier3', '')
        tier4 = lib_config.get('Tier4', '')
        tier5 = lib_config.get('Tier5', '')
        
        lib_level = 3
        if lib_name == tier4:
            lib_level = 4
        elif lib_name == tier5:
            lib_level = 5
        
        # 获取所有系列
        all_series = self.api.get_library_series(library['id'])
        
        for series in all_series:
            self._process_series(
                series,
                lib_root,
                lib_level,
                tier3,
                tier4,
                tier5,
                lib_config
            )
        
        # 清理空目录
        lib_path = lib_root.replace('/data/', lib_config.get('prefix-path', ''))
        clean_empty_folders(lib_path, self.config.manga_types)
    
    def _process_series(
        self,
        series: dict,
        lib_root: str,
        lib_level: int,
        tier3: str,
        tier4: str,
        tier5: str,
        lib_config: dict
    ):
        """
        处理单个系列
        
        Args:
            series: 系列信息
            lib_root: 库根目录
            lib_level: 库等级
            tier3-5: 等级标签
            lib_config: 库配置
        """
        books = self.api.get_series_books(series['id'])
        
        for book in books:
            if book.get('deleted'):
                continue
            
            self._process_book(
                book,
                lib_root,
                lib_level,
                tier3,
                tier4,
                tier5,
                lib_config
            )
    
    def _process_book(
        self,
        book: dict,
        lib_root: str,
        lib_level: int,
        tier3: str,
        tier4: str,
        tier5: str,
        lib_config: dict
    ):
        """
        处理单个本子
        
        Args:
            book: 本子信息
            lib_root: 库根目录
            lib_level: 库等级
            tier3-5: 等级标签
            lib_config: 库配置
        """
        metadata = book['metadata']
        path = book['url']
        chapter_tags = metadata.setdefault('tags', [])
        
        changed = False
        
        # 统计星级标签
        has_t3 = tier3 in chapter_tags
        has_t4 = tier4 in chapter_tags
        has_t5 = tier5 in chapter_tags
        tag_count = sum([has_t3, has_t4, has_t5])
        
        # 处理星级标签
        if tag_count == 0:
            # 没有星级，添加对应等级
            if lib_level == 4:
                chapter_tags.append(tier4)
                changed = True
            elif lib_level == 5:
                chapter_tags.append(tier5)
                changed = True
                
        elif tag_count == 1:
            # 有一个星级，检查是否匹配
            if lib_level != self._get_tag_level(has_t3, has_t4, has_t5):
                # 不匹配，需要移动
                self._move_to_tier(
                    path,
                    lib_root,
                    tier3 if has_t3 else (tier4 if has_t4 else tier5),
                    lib_config
                )
                return
        else:
            # 多个星级
            series_title = book.get('seriesTitle', '')
            book_name = book.get('name', '')
            logger.warning(f"多个星级标签 {chapter_tags} - {series_title} / {book_name}")
            return
        
        # 处理作者信息
        series_title = book.get('seriesTitle', '')
        tags = parse_tags_from_name(series_title)
        
        if not tags:
            logger.warning(f"无法解析标签: {series_title} / {book.get('name', '')}")
            return
        
        # 添加作者
        writer = tags[0]
        writer_meta = {"name": writer, "role": "writer"}
        
        if writer_meta not in metadata.get('authors', []):
            logger.info(f"添加作者: {writer} - {series_title} / {book.get('name', '')}")
            metadata.setdefault('authors', []).append(writer_meta)
            changed = True
        
        # 更新元数据
        if changed:
            self.api.update_book_metadata(book['id'], metadata)
        
        # 调整目录结构（添加作者目录）
        if lib_level > 3:
            self._adjust_folder_structure(
                path,
                lib_root,
                writer,
                lib_config
            )
    
    def _get_tag_level(self, has_t3: bool, has_t4: bool, has_t5: bool) -> int:
        """获取标签对应的等级"""
        if has_t3:
            return 3
        elif has_t4:
            return 4
        elif has_t5:
            return 5
        return 3
    
    def _move_to_tier(
        self,
        path: str,
        lib_root: str,
        tier: str,
        lib_config: dict
    ):
        """
        移动到指定等级目录
        
        Args:
            path: 文件路径
            lib_root: 库根目录
            tier: 目标等级
            lib_config: 库配置
        """
        prefix_path = lib_config.get('prefix-path', '')
        lib_path = lib_config.get('lib-path', '')
        
        abs_path = path.replace('/data/', prefix_path)
        dest_root = lib_path + tier
        dest_path = path.replace(lib_root, dest_root)
        
        if not self.config.debug:
            logger.info(f"移动到等级目录: {abs_path} -> {dest_path}")
            rename_file(abs_path, dest_path)
        else:
            logger.info(f"[调试模式] 移动到等级目录: {abs_path} -> {dest_path}")
    
    def _adjust_folder_structure(
        self,
        path: str,
        lib_root: str,
        writer: str,
        lib_config: dict
    ):
        """
        调整文件夹结构（添加作者目录）
        
        Args:
            path: 文件路径
            lib_root: 库根目录
            writer: 作者名
            lib_config: 库配置
        """
        prefix_path = lib_config.get('prefix-path', '')
        
        # 解析路径结构
        relative = path.replace(lib_root, '')
        parts = os.path.normpath(relative).split(os.path.sep)
        levels = len(parts)
        
        if levels > 3 and parts[levels - 4] != '':
            logger.warning(f"目录结构异常: {path}")
            return
        
        manga_zip = parts[levels - 1] if levels > 0 else None
        manga_folder = parts[levels - 2] if levels > 1 else None
        author_folder = parts[levels - 3] if levels > 2 else None
        
        # 如果作者目录不匹配，调整
        if author_folder != writer:
            author_folder = writer
        
        new_path = os.path.join(lib_root, author_folder, manga_folder, manga_zip)
        
        if new_path != path:
            abs_path = path.replace('/data/', prefix_path)
            new_abs_path = new_path.replace('/data/', prefix_path)
            
            if not self.config.debug:
                logger.info(f"调整作者目录: {abs_path} -> {new_abs_path}")
                rename_file(abs_path, new_abs_path)
            else:
                logger.info(f"[调试模式] 调整作者目录: {abs_path} -> {new_abs_path}")


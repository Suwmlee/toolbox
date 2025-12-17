# -*- coding: utf-8 -*-
"""
文件操作工具
"""
import os
import shutil
import zipfile
from typing import List
from core.constants import DEFAULT_EXCLUDE, SPECIAL_CHAPTERS, ZIP_TYPES
from core.logger import logger


def find_all_matches(root: str, exclude_list: List[str] = None) -> List[str]:
    """
    查找目录下所有符合条件的文件夹
    
    Args:
        root: 根目录
        exclude_list: 排除列表
        
    Returns:
        匹配的目录列表
    """
    if exclude_list is None:
        exclude_list = []
    
    matched = []
    exclude = DEFAULT_EXCLUDE + exclude_list
    
    try:
        dirs = os.listdir(root)
        for entry in dirs:
            if entry not in exclude:
                matched.append(entry)
    except FileNotFoundError:
        logger.error(f"目录不存在: {root}")
    except Exception as e:
        logger.error(f"读取目录失败: {e}")
    
    return matched


def find_manga_chapters(root: str) -> List[str]:
    """
    获取目录下的所有有效章节
    
    Args:
        root: 漫画根目录
        
    Returns:
        章节列表
    """
    chapters = []
    dirs = find_all_matches(root)
    
    for entry in dirs:
        full_path = os.path.join(root, entry)
        
        # 忽略特殊章节
        if any(special in entry for special in SPECIAL_CHAPTERS):
            continue
        
        if os.path.isdir(full_path):
            chapters.append(entry)
        else:
            # 检查是否为压缩文件
            if entry.lower().endswith(tuple(ZIP_TYPES)):
                chapter_name = os.path.splitext(entry)[0]
                chapters.append(chapter_name)
    
    return chapters


def rename_file(src: str, dst: str):
    """
    移动/重命名文件
    
    Args:
        src: 源文件路径
        dst: 目标文件路径
    """
    if src == dst:
        return
    
    if not os.path.exists(src):
        raise ValueError(f"源文件不存在: {src}")
    
    # 确保目标目录存在
    dst_dir = os.path.dirname(dst)
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
    
    shutil.move(src, dst)
    logger.info(f"移动文件: {src} -> {dst}")


def zip_folder(src_folder: str, dest_file: str):
    """
    压缩文件夹
    
    Args:
        src_folder: 源文件夹
        dest_file: 目标压缩文件
    """
    dest_folder = os.path.dirname(dest_file)
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
    
    if os.path.exists(dest_file):
        logger.warning(f"跳过压缩，文件已存在: {dest_file}")
        return
    
    with zipfile.ZipFile(dest_file, 'w', zipfile.ZIP_DEFLATED) as z:
        dirs = os.listdir(src_folder)
        for entry in dirs:
            file_path = os.path.join(src_folder, entry)
            
            # 跳过目录和特殊文件
            if os.path.isdir(file_path) or entry == '.nomedia':
                continue
            
            z.write(file_path, entry)
    
    logger.info(f"压缩完成: {src_folder} -> {dest_file}")


def clean_empty_folders(folder: str, valid_suffixes: List[str]) -> bool:
    """
    递归删除没有有效文件的目录
    
    Args:
        folder: 要检查的文件夹
        valid_suffixes: 有效文件后缀列表
        
    Returns:
        该文件夹是否包含有效文件
    """
    has_valid_file = False
    
    try:
        entries = os.listdir(folder)
    except Exception as e:
        logger.error(f"读取目录失败: {folder}, {e}")
        return False
    
    for entry in entries:
        full_path = os.path.join(folder, entry)
        
        if os.path.isdir(full_path):
            if clean_empty_folders(full_path, valid_suffixes):
                has_valid_file = True
        elif os.path.splitext(full_path)[1].lower() in valid_suffixes:
            has_valid_file = True
    
    if not has_valid_file:
        logger.info(f"删除空目录: {folder}")
        shutil.rmtree(folder)
    
    return has_valid_file


def get_folder_depth(path: str, current_depth: int = 0) -> int:
    """
    获取文件夹深度
    
    Args:
        path: 文件夹路径
        current_depth: 当前深度
        
    Returns:
        最大深度
    """
    if not os.path.isdir(path):
        return current_depth
    
    max_depth = current_depth
    
    try:
        for entry in os.listdir(path):
            full_path = os.path.join(path, entry)
            depth = get_folder_depth(full_path, current_depth + 1)
            max_depth = max(max_depth, depth)
    except Exception as e:
        logger.error(f"读取目录深度失败: {path}, {e}")
    
    return max_depth


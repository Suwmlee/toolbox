# -*- coding: utf-8 -*-
"""
名称处理工具
"""
import re
from typing import List, Tuple
from core.logger import logger


def replace_parentheses(text: str) -> str:
    """
    替换中文括号为英文括号
    
    Args:
        text: 原始文本
        
    Returns:
        替换后的文本
    """
    text = text.replace('（', '(').replace('）', ')')
    text = text.replace('【', '[').replace('】', ']')
    return text


def regex_match(text: str, pattern: str) -> List[str]:
    """
    正则匹配
    
    Args:
        text: 要匹配的文本
        pattern: 正则表达式
        
    Returns:
        匹配结果列表
    """
    prog = re.compile(pattern, re.IGNORECASE | re.X | re.S)
    return prog.findall(text)


def update_manga_name(original: str, groups: List[str], bad_tags: List[str]) -> str:
    """
    更新漫画名称
    
    Args:
        original: 原始名称
        groups: 需要移除的组名列表
        bad_tags: 需要排序的标签列表
        
    Returns:
        更新后的名称
    """
    name = replace_parentheses(original)
    
    # 移除组名
    for group in groups:
        name = name.replace(group, '')
    
    # 移除C开头的数字编号
    name = re.sub(r'C\d{2}', '', name, flags=re.IGNORECASE)
    
    # 重新排序标签
    tags = regex_match(name, r'\[(.*?)\]')
    if tags:
        retagged_name = name
        bad_tag_list = []
        
        # 找出需要移到后面的标签
        for tag in tags:
            for bad in bad_tags:
                if bad in tag:
                    bad_tag_list.append(tag)
                    break
        
        # 移动标签到末尾
        for tag in bad_tag_list:
            retagged_name = retagged_name.replace(f'[{tag}]', '')
            retagged_name = retagged_name + f'[{tag.strip("-_ ")}]'
        
        if retagged_name != name:
            logger.debug(f"重新排序标签: {name} -> {retagged_name}")
            name = retagged_name
    
    # 清理多余符号
    name = name.replace('[漢化]', '').replace('[汉化]', '')
    name = name.replace('[]', '').replace('()', '').replace('] [', '][').strip()
    
    # 合并多个空格
    name = ' '.join(name.split())
    
    if name != original:
        logger.info(f"更新漫画名: {original} -> {name}")
    
    return name


def update_chapter_name(original: str) -> str:
    """
    更新章节名称
    
    Args:
        original: 原始章节名
        
    Returns:
        更新后的章节名
    """
    # 特殊情况：第一话后跟随整个漫画名
    if original.startswith('_第1話'):
        logger.debug(f"第一话特殊处理: {original} -> 1")
        return '1'
    
    if ' ' not in original:
        return original
    
    new_chapter = original
    
    # 处理Tachiyomi格式
    if new_chapter.startswith('_第') or new_chapter.startswith('_Ch'):
        new_chapter = new_chapter[new_chapter.index(' '):].strip()
    
    new_chapter = new_chapter.replace(' - ', ' ')
    
    # 处理"第xxx話"格式
    matches = regex_match(new_chapter, r'第[\d]*話')
    if matches:
        logger.debug("处理'第xxx話'格式")
        number = matches[0].strip('第話')
        new_chapter = new_chapter.replace(matches[0], number)
        
        # 检查是否有重复数字
        parts = new_chapter.split(' ')
        if len(parts) > 1 and parts[0].isdigit() and parts[1].isdigit():
            logger.debug("移除重复数字")
            new_chapter = new_chapter[new_chapter.index(' '):].strip()
    
    new_chapter = new_chapter.strip('-_')
    
    if original != new_chapter:
        logger.info(f"更新章节名: {original} -> {new_chapter}")
    
    return new_chapter


def parse_tags_from_name(name: str) -> List[str]:
    """
    从名称中解析标签
    
    Args:
        name: 漫画名称
        
    Returns:
        标签列表
    """
    return regex_match(name, r'\[(.*?)\]')


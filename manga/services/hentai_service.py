# -*- coding: utf-8 -*-
"""
H-Manga 按作者整理服务

源目录格式: [作者] 漫画名  (位于 H-Manga 根目录下)
目标目录:   Hentai/Manga/<作者>/漫画名
规则:
  - 同一作者有 2 个或以上作品才移动
  - 目标目录已存在对应作者文件夹则直接放入，否则创建
"""
import os
import re
import shutil
from collections import defaultdict
from typing import Dict, List, Optional, Set
from core.config import Config
from core.logger import logger


# 匹配 "[作者] 漫画名" 最外层方括号内的作者
_AUTHOR_RE = re.compile(r'^\[([^\[\]]+)\]')


def _extract_author(name: str) -> Optional[str]:
    """从条目名称中提取作者，失败返回 None"""
    m = _AUTHOR_RE.match(name)
    if not m:
        return None
    return m.group(1).strip()


class HentaiService:
    """H-Manga 按作者整理服务"""

    def __init__(self, config: Config):
        self.config = config
        cfg = config.hentai_manga
        self.src_dir: str = cfg.get('src', '')
        self.dst_dir: str = cfg.get('dst', '')

    def organize(self):
        """执行整理（受 config.debug 控制是否真正移动）"""
        if not self.src_dir or not os.path.isdir(self.src_dir):
            logger.error(f"源目录不存在或未配置: {self.src_dir}")
            return
        if not self.dst_dir:
            logger.error("目标目录未配置 (hentai-manga.dst)")
            return

        # ── 1. 扫描源目录，按作者分组 ──────────────────────────────────
        author_works: Dict[str, List[str]] = defaultdict(list)
        no_author: List[str] = []

        for entry in sorted(os.listdir(self.src_dir)):
            full = os.path.join(self.src_dir, entry)
            if not os.path.exists(full):
                continue
            author = _extract_author(entry)
            if author:
                author_works[author].append(entry)
            else:
                no_author.append(entry)

        # ── 2. 统计 ─────────────────────────────────────────────────────
        multi = {a: works for a, works in author_works.items() if len(works) >= 2}
        single = {a: works for a, works in author_works.items() if len(works) == 1}

        logger.info(f"源目录: {self.src_dir}")
        logger.info(f"目标目录: {self.dst_dir}")
        logger.info(f"共扫描到 {sum(len(w) for w in author_works.values())} 个带作者条目")
        logger.info(f"  - 作者有多部作品（将移动）: {len(multi)} 位作者, {sum(len(w) for w in multi.values())} 部")
        logger.info(f"  - 作者仅单部作品（跳过）:   {len(single)} 位作者")
        if no_author:
            logger.info(f"  - 无法识别作者（跳过）:   {len(no_author)} 个条目")
        logger.info("")

        # ── 3. 已存在的作者目录 ─────────────────────────────────────────
        existing_authors: Set[str] = set()
        if os.path.isdir(self.dst_dir):
            existing_authors = set(os.listdir(self.dst_dir))

        # ── 4. 打印/执行移动 ────────────────────────────────────────────
        debug = self.config.debug
        mode_tag = "[调试]" if debug else "[执行]"

        for author, works in sorted(multi.items()):
            author_in_dst = author in existing_authors
            status = "已存在" if author_in_dst else "新建"
            logger.info(f"作者: {author}  ({status}，共 {len(works)} 部)")

            for work in works:
                src_path = os.path.join(self.src_dir, work)
                author_dir = os.path.join(self.dst_dir, author)
                dst_path = os.path.join(author_dir, work)
                logger.info(f"  {mode_tag} {src_path}")
                logger.info(f"         -> {dst_path}")

                if not debug:
                    os.makedirs(author_dir, exist_ok=True)
                    shutil.move(src_path, dst_path)
                    logger.info(f"         ✓ 已移动")

            logger.info("")

        # ── 5. 打印跳过明细（单作品） ───────────────────────────────────
        logger.info("── 跳过（每位作者仅一部作品）──")
        for author, works in sorted(single.items()):
            logger.info(f"  {author}: {works[0]}")

        if no_author:
            logger.info("")
            logger.info("── 跳过（无法识别作者）──")
            for entry in no_author:
                logger.info(f"  {entry}")

        logger.info("")
        if debug:
            logger.info("调试模式：以上为预览，未实际移动任何文件。")
        else:
            logger.info("整理完成。")

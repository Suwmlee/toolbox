# -*- coding: utf-8 -*-
"""
H-Manga 按作者整理服务

源目录格式: [作者] 漫画名  (位于 H-Manga 根目录下)
目标目录:   Hentai/Manga/<作者>/漫画名
规则:
  - 目标目录已存在该作者文件夹 → 无论几部，直接移入
  - 目标目录不存在该作者       → 仅当源目录有 ≥2 部时才移入（并新建文件夹）
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

        # ── 2. 已存在的作者目录 ─────────────────────────────────────────
        existing_authors: Set[str] = set()
        if os.path.isdir(self.dst_dir):
            existing_authors = set(os.listdir(self.dst_dir))

        # ── 3. 决定哪些作者需要移动 ─────────────────────────────────────
        # 已存在于目标目录：无论几部都移
        # 不存在于目标目录：需要 ≥2 部才移
        to_move: Dict[str, List[str]] = {}
        skip_single: Dict[str, List[str]] = {}

        for author, works in author_works.items():
            if author in existing_authors or len(works) >= 2:
                to_move[author] = works
            else:
                skip_single[author] = works

        total_move_works = sum(len(w) for w in to_move.values())
        existing_move = {a for a in to_move if a in existing_authors}
        new_move = {a for a in to_move if a not in existing_authors}

        logger.info(f"源目录: {self.src_dir}")
        logger.info(f"目标目录: {self.dst_dir}")
        logger.info(f"共扫描到 {sum(len(w) for w in author_works.values())} 个带作者条目")
        logger.info(f"  - 将移动：{len(to_move)} 位作者，{total_move_works} 部")
        logger.info(f"    其中目标已存在（直接放入）: {len(existing_move)} 位")
        logger.info(f"    其中目标不存在（新建文件夹，≥2部）: {len(new_move)} 位")
        logger.info(f"  - 跳过（目标不存在且仅单部）: {len(skip_single)} 位作者")
        if no_author:
            logger.info(f"  - 无法识别作者（跳过）: {len(no_author)} 个条目")
        logger.info("")

        # ── 4. 打印/执行移动 ────────────────────────────────────────────
        debug = self.config.debug
        mode_tag = "[调试]" if debug else "[执行]"

        for author, works in sorted(to_move.items()):
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

        # ── 5. 打印跳过明细 ─────────────────────────────────────────────
        logger.info("── 跳过（目标不存在且仅一部作品）──")
        for author, works in sorted(skip_single.items()):
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

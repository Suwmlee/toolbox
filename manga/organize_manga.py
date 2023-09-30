#!/bin/python3
# -*- coding: utf-8 -*-

import argparse
import os
from mangainfo import MangaInfo
from utils import fix_series, fix_tankobon, loadConfig, renamefile, zipfolder

TEST_MODE = True


def organize(config):
    """ 整理
    """
    for src in config['folders']:
        if not os.path.exists(src):
            print(f"[!] 目录异常 {src}")
            return
        dirs = os.listdir(src)
        for entry in dirs:
            if entry == '@eaDir':
                print("[x] 忽略群晖文件夹")
                continue
            full = os.path.join(src, entry)
            depth = get_depth(full)

            if depth == 1:
                print(f"[+] 分析: {full}")
                organize_manga(full, src)
            elif depth == 2:
                print(f"[+] 两级目录,可能含有作者层级: {full}")
                deps = os.listdir(full)
                for ent in deps:
                    print(f"[-] 两级目录: {ent}")
                    absf = os.path.join(full, ent)
                    organize_manga(absf, full)
            else:
                print(f"[!] 超过三个层级 {full}")
                print(f"[!] 超过三个层级 {full}")


def get_depth(path, depth=0):
    if not os.path.isdir(path): return depth
    maxdepth = depth
    for entry in os.listdir(path):
        fullpath = os.path.join(path, entry)
        maxdepth = max(maxdepth, get_depth(fullpath, depth + 1))
    return maxdepth


def organize_manga(root, dst_folder):
    """ 整理单个漫画目录
    """
    mangaInfo = MangaInfo(root)

    if mangaInfo.isManga:
        mangaInfo.dstFolder = dst_folder
        modified = fix_manga_folder(mangaInfo, config)
        if not modified:
            print("[-] 跳过... \n")
            return
        # print("[-] 开始移动...")
        for key in modified.keys():
            source = key
            dest = modified.get(key) + '.zip'
            is_zip = False
            # 大小写敏感
            for ztype in ['.zip', '.cbz', '.pdf', '.PDF']:
                if os.path.exists(key + ztype):
                    source = key + ztype
                    dest = modified.get(key) + ztype
                    is_zip = True
                    break
            if is_zip:
                if source == dest:
                    continue
                if TEST_MODE:
                    print(f"[!] 测试模式： {source} 到 {dest}")
                    continue
                print(f"[-] 是压缩文件,直接移动到 {dest}")
                renamefile(source, dest)
            else:
                if TEST_MODE:
                    print(f"[!] 测试模式： {source} 到 {dest}")
                    continue
                zipfolder(source, dest)
        print("[-] 整理完成!\n")


def fix_manga_folder(mangaInfo: MangaInfo, config):
    """ 获取移动的章节列表
    """
    if mangaInfo.isTankobon:
        return fix_tankobon(mangaInfo.fullPath, mangaInfo.name, mangaInfo.chapters,
                            config['groups'], config['tags'], mangaInfo.dstFolder)
    else:
        return fix_series(mangaInfo.fullPath, mangaInfo.name, mangaInfo.chapters,
                          config['groups'], config['tags'], mangaInfo.dstFolder)


if __name__ == "__main__":
    config = loadConfig()

    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--test', action='store_true', help='测试模式')
    parser.add_argument('-f', '--force', action='store_true', help='强制移动')
    args = parser.parse_args()

    if args.test:
        TEST_MODE = True
    else:
        TEST_MODE = config['dry-run']
    if args.force:
        TEST_MODE = False

    organize(config['organize-manga'])

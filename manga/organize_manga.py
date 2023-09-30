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
                # organize_manga(full, src)
            elif depth == 2:
                print("[!] 两级目录,可能含有作者层级")
                deps = os.listdir(full)
                for ent in deps:
                    absfull = os.path.join(full, ent)
                    print(f"[+] 两级目录: {absfull}")
            else:
                print("[!] 超过三个层级")


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
        print("[-] 开始压缩...")
        for key in modified.keys():
            cbzfile = key + '.cbz'
            dest = modified.get(key) + '.zip'
            if TEST_MODE:
                print(f"[!] 测试模式： {cbzfile} 到 {dest}")
            else:
                if os.path.exists(cbzfile):
                    print(f"[-] 已经存在cbz文件,直接移动 {cbzfile} 到 {dest}")
                    renamefile(cbzfile, dest)
                else:
                    zipfolder(key, dest)
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

    organize(config['organize-manga'])

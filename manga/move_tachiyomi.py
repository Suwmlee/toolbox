#!/bin/python3
# -*- coding: utf-8 -*-

import argparse
import os
import re
from mangainfo import MangaInfo
from utils import loadConfig, renamefile, zipfolder, updateChapter, updateMangaName

TEST_MODE = True


def moveManga(config):
    """
    -   load all manga folder
    -   check manga type one-by-one
    -   analysis move/keep
    -   keep: pass / move: dst
    -   fix name and chapter
    -   zip and move
    """
    for src in config['sources']:
        if not os.path.exists(src):
            print(f"[!] tachiyomi: src目录异常 {src}")
            return
        dirs = os.listdir(src)
        for entry in dirs:
            if entry == '@eaDir':
                print("[x] 忽略群晖文件夹")
                continue
            full = os.path.join(src, entry)
    
            print(f"[+] 分析: {entry}")
            mangaInfo = MangaInfo(full)
            if mangaInfo.isManga:
                mangaInfo.analysisManga(config)
                print(f"[-] 类型 {mangaInfo.typeName} 完结 {mangaInfo.ended}")
            else:
                print("[-] 非漫画\n")
                continue

            if mangaInfo.keepTag:
                print(f"[-] 不移动，跳过\n")
                continue
            else:
                modified = moveMangaChapterList(mangaInfo, config)
                if not modified:
                    print("[-] 跳过... \n")
                    continue
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


def moveMangaChapterList(mangaInfo: MangaInfo, config):
    """ 获取移动的章节列表
    """
    # 修正漫画名字
    modifiedManga = dict()

    manganame = updateMangaName(mangaInfo.name, config['groups'], config['tags'])
    if mangaInfo.isTankobon:
        # 单本 将第一章节直接输出为漫画目录即可
        sourcepath = os.path.join(mangaInfo.fullPath, mangaInfo.chapters[0])
        newpath = os.path.join(mangaInfo.dstFolder, manganame, manganame)
        print(f"[-] 单本漫画整理:  {mangaInfo.chapters[0]} >>> {manganame}")
        modifiedManga[sourcepath] = newpath
    else:
        for ch in mangaInfo.chapters:
            newch = updateChapter(ch)
            oldpath = os.path.join(mangaInfo.fullPath, ch)
            newpath = os.path.join(mangaInfo.dstFolder, manganame, newch)
            modifiedManga[oldpath] = newpath
    return modifiedManga


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
    moveManga(config['tachiyomi'])

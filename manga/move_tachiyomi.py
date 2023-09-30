#!/bin/python3
# -*- coding: utf-8 -*-

import argparse
import os
import re
from mangainfo import MangaInfo
from utils import loadConfig, regexMatch, renamefile, replaceParentheses, zipfolder

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
                modified = moveMangaChapterList(mangaInfo)
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


def moveMangaChapterList(mangaInfo: MangaInfo):
    """ 获取移动的章节列表
    """
    # 修正漫画名字
    modifiedManga = dict()

    manganame = updateMangaName(mangaInfo.name)
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


def updateMangaName(orignal):
    """ 更新漫画名
    """
    # print(f"原始漫画名: {orignal}")
    name = replaceParentheses(orignal)
    replaces = ['DL版', '个人整理制作版', '個人整合', '禁漫掃圖組', '風的工房',
                '中國翻訳', '中国翻訳']
    for r in replaces:
        name = name.replace(r, '')
    name = re.sub('C\d{2}', '', name, re.IGNORECASE)
    # 更改[]顺序
    results = regexMatch(name, '\[(.*?)\]')
    if results:
        retagname = name
        sorts = ['汉化', '漢化', '無碼', '全彩', '薄碼', '個人', '无修正']
        retags = []
        for tag in results:
            for s in sorts:
                if s in tag:
                    retags.append(tag)
        for stag in retags:
            retagname = retagname.replace('['+stag+']', '')
            retagname = retagname + '[' + stag.strip('-_ ')+']'
        if retagname != name:
            print(f"[-] 重新排序tag  {name} {retagname}")
            name = retagname
    name = name.replace('[漢化]', '').replace('[汉化]', '')
    name = name.replace('[]', '').replace('()', '').replace('] [', '][').strip()
    # 多空格合并
    name = ' '.join(name.split())
    if name != orignal:
        print(f"[-] 更新漫画名: {orignal} >>> {name}")
    return name


def updateChapter(orignal: str):
    """ 更新章节名
    """
    if orignal.startswith('_第1話'):
        print("[-] 第一话 空格后跟随整个漫画名 需要特殊处理")
        print(f"[-] 章节更新:  {orignal} >>> 1 ")
        return '1'
    elif ' ' in orignal:
        newch = orignal
        if newch.startswith('_第') or newch.startswith('_Ch'):
            # tachiyomi 下载格式
            newch = newch[newch.index(' '):].strip()
        newch = newch.replace(' - ', ' ')
        results = regexMatch(newch, '第[\d]*話')
        if results:
            print("[-] 章节存在特殊情况 第xxx話")
            num = results[0].strip('第話')
            newch = newch.replace(results[0], num)
            tmps = newch.split(' ')
            if len(tmps) > 1 and tmps[0].isdigit() and tmps[1].isdigit():
                print("[-] 开头为两个数字 剔除 `第xxx話 第xxx話` `第xxx話 xxx` ")
                newch = newch[newch.index(' '):].strip()
        newch = newch.strip('-_')
        if orignal != newch:
            print(f"[-] 章节更新:  {orignal} >>> {newch}")
        return newch
    else:
        # print(f"不需要更新 {orignal} 可能是特殊情况")
        return orignal


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

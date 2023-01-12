#!/bin/python3
# -*- coding: utf-8 -*-

import os
import re
from utils import loadConfig, regexMatch, renamefile, replaceParentheses, zipfolder

DEBUG_MODE = True


class MangaInfo():

    def __init__(self, root: str):
        self.isManga = True
        self.fullPath = root
        self.name = os.path.basename(root)
        self.chapters = findMangaChapter(root)
        # 检测单本，多本
        if len(self.chapters) < 1:
            self.isManga = False
            return
        if checkIfTankobonByChapter(self.chapters):
            self.isTanbokon = True
            self.isSeries = False
        else:
            self.isTanbokon = False
            self.isSeries = True

    def initExtra(self):
        self.typeName = None
        self.ended = False

        self.keepTag = True
        self.dstFolder = ''

    def analysisManga(self, config):
        self.initExtra()
        self.analysisMangaType(config)
        self.queryMangaMapping(config)

    def analysisMangaType(self, config):
        """ 
        type: name, folder, tanbokon, series
        """
        # 从上往下依次判断
        for filter in config['filters']:
            if filter['type'] == 'name':
                if self.name in filter['names']:
                    self.typeName = filter['name']
                if self.name in filter['ended']:
                    self.ended = True
            elif filter['type'] == 'folder':
                for folder in filter['folders']:
                    if self.fullPath.startswith(folder):
                        self.typeName = filter['name']
                        break
                if self.name in filter['ended']:
                    self.ended = True
            elif filter['type'] == 'tanbokon':
                if self.isTanbokon:
                    self.typeName = filter['name']
                if self.name in filter['ended']:
                    self.ended = True
            elif filter['type'] == 'series':
                if self.isSeries:
                    self.typeName = filter['name']
                if self.name in filter['ended']:
                    self.ended = True

    def queryMangaMapping(self, config):
        """ 查询漫画映射
        """
        for map in config['mapping']:
            if map['name'] == self.typeName:
                if self.ended:
                    flag = map['ended']
                else:
                    flag = map['default']
                if flag == 'move':
                    self.dstFolder = map['dst']
                    self.keepTag = False
                break

    def moveMangaChapterList(self):
        """ 获取移动的章节列表
        """
        # 修正漫画名字
        modifiedManga = dict()

        manganame = updateMangaName(self.name)
        if self.isTanbokon:
            # 单本 将第一章节直接输出为漫画目录即可
            sourcepath = os.path.join(self.fullPath, self.chapters[0])
            newpath = os.path.join(self.dstFolder, manganame, manganame)
            print(f"单本漫画整理:  {self.chapters[0]} >>> {manganame}")
            modifiedManga[sourcepath] = newpath
        else:
            for ch in self.chapters:
                newch = updateChapter(ch)
                oldpath = os.path.join(self.fullPath, ch)
                newpath = os.path.join(self.dstFolder, manganame, newch)
                modifiedManga[oldpath] = newpath
        return modifiedManga


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

            mangaInfo = MangaInfo(full)
            if mangaInfo.isManga:
                mangaInfo.analysisManga(config)
            else:
                continue

            if mangaInfo.keepTag:
                continue
            else:
                modified = mangaInfo.moveMangaChapterList()
                if not modified:
                    print("跳过... \n")
                    continue
                print("开始压缩...")
                for key in modified.keys():
                    cbzfile = key + '.cbz'
                    dest = modified.get(key) + '.zip'
                    if DEBUG_MODE:
                        print(f"测试模式： {cbzfile} 到 {dest}")
                    else:
                        if os.path.exists(cbzfile):
                            print(f"已经存在cbz文件,直接移动 {cbzfile} 到 {dest}")
                            renamefile(cbzfile, dest)
                        else:
                            zipfolder(key, dest)
                print(f"整理完成! {full} \n")


def findMangaChapter(root):
    """ 获取目录下的所有有效章节
    """
    dirs = os.listdir(root)
    chapters = []
    for entry in dirs:
        if entry == '@eaDir':
            print("忽略群晖文件夹")
            continue
        if entry.endswith('_tmp'):
            print("忽略临时文件夹")
            continue
        full = os.path.join(root, entry)
        # 忽略 停刊公告/休刊公告/休刊通知 文件夹
        if '停刊公告' in entry or '休刊公告' in entry or '休刊通知' in entry:
            continue
        if os.path.isdir(full):
            chapters.append(entry)
        else:
            if entry.endswith('.cbz'):
                # print("漫画目录已经是压缩文件")
                chapter = os.path.splitext(entry)[0]
                chapters.append(chapter)
    return chapters


def checkIfTankobonByChapter(chapters):
    # 区分单本,多章节,合集等
    isTankobon = False
    if len(chapters) == 0:
        print("未检测到章节")
        return None
    elif len(chapters) < 2:
        if chapters[0] == '_单章节' or chapters[0] == '单章节':
            print("是单本漫画")
            isTankobon = True
        elif chapters[0] == '_Ch. 1' or chapters[0] == 'Ch. 1':
            print("可能是单本漫画,目前只有一个章节")
            isTankobon = True
    return isTankobon


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
            print(f"重新排序tag  {name} {retagname}")
            name = retagname
    name = name.replace('[漢化]', '').replace('[汉化]', '')
    name = name.replace('[]', '').replace('()', '').replace('] [', '][').strip()
    # 多空格合并
    name = ' '.join(name.split())
    if name != orignal:
        print(f"更新漫画名: {orignal} >>> {name}")
    return name


def updateChapter(orignal: str):
    """ 更新章节名
    """
    if orignal.startswith('_第1話'):
        print("第一话 空格后跟随整个漫画名 需要特殊处理")
        print(f"章节更新:  {orignal} >>> 1 ")
        return '1'
    elif ' ' in orignal:
        newch = orignal
        if newch.startswith('_第') or newch.startswith('_Ch'):
            # tachiyomi 下载格式
            newch = newch[newch.index(' '):].strip()
        newch = newch.replace(' - ', ' ')
        results = regexMatch(newch, '第[\d]*話')
        if results:
            print("章节存在特殊情况 第xxx話")
            num = results[0].strip('第話')
            newch = newch.replace(results[0], num)
            tmps = newch.split(' ')
            if len(tmps) > 1 and tmps[0].isdigit() and tmps[1].isdigit():
                print("开头为两个数字 剔除 `第xxx話 第xxx話` `第xxx話 xxx` ")
                newch = newch[newch.index(' '):].strip()
        newch = newch.strip('-_')
        if orignal != newch:
            print(f"章节更新:  {orignal} >>> {newch}")
        return newch
    else:
        # print(f"不需要更新 {orignal} 可能是特殊情况")
        return orignal


if __name__ == "__main__":

    localPath = os.path.dirname(os.path.abspath(__file__))
    configPath = os.path.join(localPath, 'manga.yaml')
    config = loadConfig(configPath)

    DEBUG_MODE = config['dry-run']

    moveManga(config['tachiyomi'])

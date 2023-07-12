#!/bin/python3
# -*- coding: utf-8 -*-
""" Optimize manga folder

管理 tachiyomi下载目录
优化文件名并压缩
转移到指定目录

整理 komga 漫画库

"""
import os
import re
import shutil
import zipfile
from yaml import load  # pip install pyyaml


def loadConfig():
    try:
        from yaml import CLoader as Loader
    except ImportError:
        from yaml import Loader
    localPath = os.path.dirname(os.path.abspath(__file__))
    data = None
    with open(os.path.join(localPath, 'manga.yaml'), mode="r", encoding="utf8") as c:
        data = load(c.read(), Loader=Loader)
    return data


def finadAllFiles(root, escape_folder: list = None):
    """ return zip/rar/pdf files under directory 'root'
    """
    for folder in escape_folder:
        if folder in root:
            return []
    total = []
    file_type = ['.zip', '.rar', '.pdf']
    dirs = os.listdir(root)
    for entry in dirs:
        f = os.path.join(root, entry)
        if os.path.isdir(f):
            total += finadAllFiles(f, escape_folder)
        elif f.lower().endswith(tuple(file_type)):
            total.append(f)
    return total


def cleanFolderWithoutSuffix(folder, suffix):
    """ 删除无匹配后缀文件的目录
    """
    if TEST_MODE:
        return
    hassuffix = False
    dirs = os.listdir(folder)
    for file in dirs:
        f = os.path.join(folder, file)
        if os.path.isdir(f):
            hastag = cleanFolderWithoutSuffix(f, suffix)
            if hastag:
                hassuffix = True
        elif os.path.splitext(f)[1].lower() in suffix:
            hassuffix = True
    if not hassuffix:
        print(f"删除无匹配后缀文件目录 [{folder}]")
        shutil.rmtree(folder)
    return hassuffix


def zipfolder(srcfolder, destfile):
    """ 压缩 `srcfolder` 目录下的文件到 `destfile`
    :param srcfolder: 需要压缩的目录,仅压缩此目录下的文件,不会深层压缩
    """
    if TEST_MODE:
        return
    destfolder = os.path.dirname(destfile)
    if not os.path.exists(destfolder):
        os.makedirs(destfolder)
    if not os.path.exists(destfile):
        z = zipfile.ZipFile(destfile, 'w', zipfile.ZIP_DEFLATED)
        dirs = os.listdir(srcfolder)
        for dir in dirs:
            filepath = os.path.join(srcfolder, dir)
            if os.path.isdir(filepath):
                continue
            if dir == '.nomedia':
                continue
            z.write(filepath, filepath)
        z.close()
    else:
        print(f"跳过压缩: 已存在压缩文件 [{destfile}]")


def renamefile(src, dst):
    """ 移动文件
    """
    if TEST_MODE:
        return
    if os.path.exists(src):
        dir = os.path.dirname(dst)
        if not os.path.exists(dir):
            os.makedirs(dir)
        shutil.move(src, dst)
    else:
        raise ValueError(f"重命名 源文件不存在 {src}")


def replaceParentheses(basestr: str):
    """ 替换特殊符号
    """
    if '（' in basestr:
        basestr = basestr.replace('（', '(')
    if '）' in basestr:
        basestr = basestr.replace('）', ')')
    if '【' in basestr:
        basestr = basestr.replace('【', '[')
    if '】' in basestr:
        basestr = basestr.replace('】', ']')
    return basestr


def regexMatch(basename, reg):
    """ 正则过滤
    """
    prog = re.compile(reg, re.IGNORECASE | re.X | re.S)
    result = prog.findall(basename)
    return result


def zipFolder(source):
    """ TODO 压缩root目录下的文件夹

    压缩后的文件夹不会嵌套文件夹
    """
    # root = os.path.dirname(__file__)
    dirs = os.listdir(source)
    for d in dirs:
        fullpath = os.path.join(source, d)
        if os.path.isdir(fullpath):
            startdir = fullpath  # 要压缩的文件夹路径
            file_news = startdir + '.zip'  # 压缩后文件夹的名字
            if not os.path.exists(file_news):
                z = zipfile.ZipFile(file_news, 'w', zipfile.ZIP_DEFLATED)  # 参数一：文件夹名
                for dirpath, dirnames, filenames in os.walk(startdir):
                    fpath = dirpath.replace(startdir, '')  # 这一句很重要，不replace的话，就从根目录开始复制
                    fpath = fpath and fpath + os.sep or ''  # 这句话理解我也点郁闷，实现当前文件夹以及包含的所有文件的压缩
                    for filename in filenames:
                        z.write(os.path.join(dirpath, filename), fpath+filename)
                        print('压缩成功: ' + d + " " + filename)
                z.close()


def changePicNameByWeight(root, weight: int):
    """ 原数字命名jpg文件,增加权重后重命名
    :param root: 目录
    :param weight: 增加的权重
    """
    dirs = os.listdir(root)
    for d in dirs:
        fullpath = os.path.join(root, d)
        name, ext = os.path.splitext(d)
        if os.path.isfile(fullpath) and ext == '.jpg':
            print(fullpath)
            newname = "%03d" % (weight+int(name))
            print("convert [{}] to [{}]".format(d, newname + ext))
            newpath = os.path.join(root, newname + ext)
            print(newpath)
            shutil.copyfile(fullpath, newpath)

#===== 整理Tachiyomi下载目录 开始 ==================


def tachiyomiManage(src, dst):
    """ 整理tachiyomi
    """
    if not os.path.exists(src) or not os.path.exists(dst):
        print(f"目录异常 {src} {dst}")
        return
    dirs = os.listdir(src)
    for entry in dirs:
        full = os.path.join(src, entry)
        if os.path.isdir(full):
            if entry == '@eaDir':
                print("忽略群晖文件夹")
                continue
            modified = tachiyomiMangaFolder(full, dst)
            if not modified:
                print("跳过... \n")
                continue
            print("开始压缩...")
            for key in modified.keys():
                cbzfile = key + '.cbz'
                dest = modified.get(key) + '.zip'
                if os.path.exists(cbzfile):
                    print(f"已经存在cbz文件,直接移动 {cbzfile} 到 {dest}")
                    renamefile(cbzfile, dest)
                else:
                    zipfolder(key, dest)
            print(f"整理完成! {full} \n")


def tachiyomiMangaFolder(root, dstfolder) -> dict:
    """
    处理tachiyomi具体漫画目录
    :param root:   tachiyomi下载目录里的具体漫画目录
    :param dstfolder:  整理后的输出目录
    :return : 整理前后对应路径
    """
    print("当前漫画目录:" + root)
    manganame = os.path.basename(root)
    # 修正漫画名字
    manganame = updateMangaName(manganame)
    dirs = os.listdir(root)
    # 先获取所有章节
    chapters = []
    for entry in dirs:
        if entry == '@eaDir':
            print("忽略群晖文件夹")
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
    modifiedManga = dict()
    # 区分单本,多章节,合集等
    isSingle = False
    if len(chapters) == 0:
        print("未检测到章节")
        return None
    elif len(chapters) < 2:
        if chapters[0] == '_单章节':
            print("是单本漫画")
            isSingle = True
        elif chapters[0] == '_Ch. 1':
            print("可能是单本漫画,目前只有一个章节")
            isSingle = True
    if isSingle:
        # 单本 将第一章节直接输出为漫画目录即可
        sourcepath = os.path.join(root, chapters[0])
        newpath = os.path.join(dstfolder, manganame, manganame)
        print(f"单本漫画整理:  {chapters[0]} >>> {manganame}")
        modifiedManga[sourcepath] = newpath
    else:
        for ch in chapters:
            newch = updateChapter(ch)
            oldpath = os.path.join(root, ch)
            newpath = os.path.join(dstfolder, manganame, newch)
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
        sorts = ['汉化', '漢化', '無碼', '全彩', '薄碼', '個人', '无修正', 'Chinese', '连载中', '完结']
        writer = results[0]
        if not writer in sorts:
            retagname = retagname.replace('[' + writer + ']', '')
            retagname = '[' + writer + '] ' + retagname
        retags = []
        for tag in results:
            for s in sorts:
                if s in tag:
                    retags.append(tag)
        for stag in retags:
            retagname = retagname.replace('['+stag+']', '')
            retagname = retagname + '[' + stag.strip('-_ ')+']'
        if retagname != name:
            # print(f"重新排序tag  {name} ==> {retagname}")
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

#===== 整理Tachiyomi下载目录 结束 ==================


def komgaMangaLib(libfolder):
    """ 整理 komga 漫画库内的文件

    komga都是zip文件, 都是两级目录
    zip一级,zip上面一级
    """
    print("开始整理漫画库:" + libfolder)
    files = finadAllFiles(libfolder, ['@eaDir'])
    for cfile in files:
        mid = str(cfile).replace(libfolder, '')
        # print(f"文件位于顶层的结构 {mid} \n")
        mids = os.path.normpath(mid).split(os.path.sep)
        # filename = os.path.splitext(os.path.basename(s))[0]
        alllvl = len(mids)
        if alllvl > 3 and mids[alllvl-4] != '':
            print(f"!!!居然有三级以上目录!!! {cfile}")
            raise
        mangazip = mids[alllvl-1] if alllvl > 0 else None
        mangafolder = mids[alllvl-2] if alllvl > 1 else None
        authorfolder = mids[alllvl-3] if alllvl > 2 else None
        mangazipname = os.path.splitext(mangazip)[0]

        author = ''
        manganame = ''
        chapter = ''
        if not mangafolder:
            manganame = mangazipname
            print(f"没有上级目录,只有zip 是单本漫画,且需要增加一级目录 {manganame}")
        elif mangazipname == mangafolder:
            manganame = mangafolder
            if authorfolder:
                author = authorfolder.strip('[]')
                print(f"合集目录 当前是单本漫画, {manganame}")
            else:
                print(f"单本漫画 文件名与上级目录相同 {manganame}")
                # TEST:增加作者文件夹,慎重增加,确认无误后再增加
                # result = regexMatch(mangafolder, '[\[](.*?)[\]]')
                # if result:
                #     author = result[0]
        else:
            if authorfolder:
                author = authorfolder.strip('[]')
            result = regexMatch(mangafolder, '[\[](.*?)[\]]')
            if result and len(result) == 1 and result[0] == mangafolder.strip('[]'):
                manganame = mangafolder
                author = result[0]
                print(f"可能是作者合集 上级目录被 [] 包住 {author} --- {manganame}")
            else:
                # 注意 是以文件夹的漫画名为准
                manganame = mangafolder
                pfolder = os.path.dirname(cfile)
                # 同目录下多少文件
                cfiles = [x for x in files if x.startswith(pfolder)]
                if len(cfiles) == 1:
                    # 只有一个文件, 单本漫画
                    chapter = mangafolder
                    print(f"可能是单本漫画 只有一本  {manganame}  --- {chapter}")
                else:
                    chapter = mangazipname
                    print(f"可能是多章节漫画  {manganame}  --- {chapter}")
        if author:
            author = '[' + author + ']'
        if manganame:
            manganame = updateMangaName(manganame)
        if chapter:
            chapter = updateChapter(chapter)
        else:
            chapter = manganame

        newpath = os.path.join(libfolder, author, manganame, chapter)
        ext = os.path.splitext(cfile)[1]
        newpath = newpath + ext
        if newpath != cfile:
            print(f"!!!更新:  {cfile} >>> {newpath}")
            renamefile(cfile, newpath)
        print("\n")


if __name__ == "__main__":

    config = loadConfig()
    TEST_MODE = config['dry-run']
    MANGA_TYPE = config['manga-type']
    print(f"漫画过滤类型: {MANGA_TYPE}")
    # 处理tachiyomi下载目录
    if TEST_MODE:
        print("当前处于测试模式")

    # if config['tachiyomi']['enable']:
    #     for tachi in config['tachiyomi']['mapping']:
    #         src = tachi['src']
    #         dst = tachi['dst']
    #         tachiyomiManage(src, dst)

    if config['komgalib']['enable']:
        for komgalib in config['komgalib']['libraries']:
            komgaMangaLib(komgalib)
            cleanFolderWithoutSuffix(komgalib, MANGA_TYPE)

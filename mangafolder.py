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

# 测试模式，不会删除/更改文件
TEST_MODE = True
MANGA_TYPE = ['.zip', '.rar', '.pdf', '.jpg', '.png', '.jpeg', '.bmp', '.gif']

def finadAllFiles(root, escape_folder:list=None):
    """ return zip/rar files under directory 'root'
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
        elif os.path.splitext(f)[1].lower() in file_type:
            total.append(f)
    return total


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


def optimizeNaming(root):
    """ 优化命名
    """
    # `[作者] 名字 [章节/完结][语言][无修]`
    files = finadAllFiles(root, '')
    for single in files:
        print("[+] 开始 " + single)
        (filefolder, filename) = os.path.split(single)
        base, ext = os.path.splitext(filename)
        filename2 = base
        # 过滤[]防止内部()
        results = regexMatch(filename2, '\[(.+?)\]')
        for i in results:
            filename2 = str(filename2).replace('[' + i + ']', '')
        # 替换剩余()符号
        filename3 = replaceParentheses(filename2)
        # 还原过滤的[]
        filename4 = str(base).replace(filename2, filename3)
        replacename = filename4
        # 提取 所有tag 标题
        tags = regexMatch(filename4, '\[(.+?)\]')
        for j in tags:
            filename4 = str(filename4).replace('[' + j + ']', '')
        manganame = filename4.strip()
        # 判断tag 是否有汉化标记
        chstag = ['中国翻訳', '汉化', '中国語', 'chinese', 'chs', 'cht']
        addchs = False
        # 剔除非规范汉化标记
        # for tag in tags:
        #     if tag in chstag:
        #         print("存在中文标记")
        #         # 剔除标记
        #         replacename = str(replacename).replace('[' + tag + ']', '')
        #         addchs = True
        # 是否增加汉化标记
        if addchs:
            finalname = replacename.replace(filename4, ' ' + manganame + ' [汉化]')
        else:
            finalname = replacename.replace(filename4, ' ' + manganame + ' ')
        finalname = finalname.strip()

        # 顶层文件增加嵌套文件夹
        midfolder = str(filefolder).replace(root, '').lstrip("\\").lstrip("/")
        if midfolder == '':
            midfolder = finalname
        
        fullpath = os.path.join(root, midfolder, finalname + ext)
        newfolder= os.path.dirname(fullpath)
        if not os.path.exists(newfolder):
            os.makedirs(newfolder)
        print("[+] 修正 " + fullpath)
        os.rename(single, fullpath)


def zipFolder(source):
    """ 压缩root目录下的文件夹

    压缩后的文件夹不会嵌套文件夹
    """
    # root = os.path.dirname(__file__)
    dirs = os.listdir(source)
    for d in dirs:
        fullpath = os.path.join(source, d)
        if os.path.isdir(fullpath):
            startdir = fullpath  #要压缩的文件夹路径
            file_news = startdir +'.zip' # 压缩后文件夹的名字
            if not os.path.exists(file_news):
                z = zipfile.ZipFile(file_news,'w',zipfile.ZIP_DEFLATED) #参数一：文件夹名
                for dirpath, dirnames, filenames in os.walk(startdir):
                    fpath = dirpath.replace(startdir,'') #这一句很重要，不replace的话，就从根目录开始复制
                    fpath = fpath and fpath + os.sep or ''#这句话理解我也点郁闷，实现当前文件夹以及包含的所有文件的压缩
                    for filename in filenames:
                        z.write(os.path.join(dirpath, filename),fpath+filename)
                        print ('压缩成功: ' + d + " " + filename)
                z.close()


def changePicName(root, start: int):
    """ 更改 jpg 名称编号
    :param root:   目录
    :param start:  起始编号
    """
    dirs = os.listdir(root)
    for d in dirs:
        fullpath = os.path.join(root, d)
        name, ext = os.path.splitext(d)
        if os.path.isfile(fullpath) and ext == '.jpg':
            print(fullpath)
            newname = "%03d" % (start+int(name))
            print("convert [{}] to [{}]".format(d, newname + ext))
            newpath = os.path.join(root, newname + ext)
            print(newpath)
            shutil.copyfile(fullpath, newpath)


def tachiyomiManga(root, dstfolder) -> dict:
    """
    处理tachiyomi下载目录下具体漫画
    :param root:   tachiyomi下载目录
    :param dstfolder:  整理后的输出目录

    """
    print("当前漫画目录:" + root)
    manganame = os.path.basename(root)
    manganame = updateMangaName(manganame)
    # 修正漫画名字
    dirs = os.listdir(root)
    chapters = []
    for entry in dirs:
        if entry == '@eaDir':
            print("忽略群晖文件夹")
            continue
        full = os.path.join(root, entry)
        if os.path.isdir(full):
            # 忽略 停刊公告/休刊公告/休刊通知 文件夹
            if '停刊公告' in entry or '休刊公告' in entry or '休刊通知' in entry:
                continue
            chapters.append(entry)
    modifiedManga = dict()
    isSingle = False
    if len(chapters) < 2:
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
    print("\n")
    return modifiedManga


def tachiyomiZip(srcfolder, dest):
    """ 压缩源文件夹到目标文件
    """
    if TEST_MODE:
        return
    destfile = dest + '.zip'
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
        print(f"跳过压缩: 已存在压缩文件 [{destfile}]")


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
    results = regexMatch(name, '[\[](.*?)[\]]')
    if results:
        retagname = name
        sorts = ['汉化','漢化','無碼','全彩','薄碼','個人','无修正']
        retags = []
        for tag in results:
            for s in sorts:
                if s in tag:
                    retags.append(tag)
        for stag in retags:
            retagname = retagname.replace('['+stag+']', '')
            retagname = retagname + '['+ stag.strip('-_ ')+']'
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
        if orignal != newch:
            print(f"章节更新:  {orignal} >>> {newch}")
        return newch
    else:
        # print(f"不需要更新 {orignal} 可能是特殊情况")
        return orignal


def komgaManga(folder):
    """ 整理 komga 漫画库内的文件
    
    komga都是zip文件, 都是两级目录
    zip一级,zip上面一级
    """
    print("开始整理漫画库:" + folder)
    files = finadAllFiles(folder, ['@eaDir'])
    for cfile in files:
        mid = str(cfile).replace(folder, '')
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
                cfiles = [ x  for x in files if x.startswith(pfolder)]
                if len(cfiles) == 1:
                    # 只有一个文件, 单本漫画
                    chapter = mangafolder
                    print(f"可能是单本漫画 只有一本  {manganame}  --- {chapter}")
                else:
                    chapter = mangazipname
                    print(f"可能是多章节漫画  {manganame}  --- {chapter}")
        if author:
            author = '['+ author +']'
        if manganame:
            manganame = updateMangaName(manganame)
        if chapter:
            chapter = updateChapter(chapter)
        else:
            chapter = manganame

        newpath = os.path.join(folder, author, manganame, chapter)
        ext = os.path.splitext(cfile)[1]
        newpath = newpath + ext
        if newpath != cfile:
            print(f"!!!更新:  {cfile} >>> {newpath}")
            renamefile(cfile, newpath)
        print("\n")

def renamefile(src, dst):
    if TEST_MODE:
        return
    if os.path.exists(src):
        dir = os.path.dirname(dst)
        if not os.path.exists(dir):
            os.makedirs(dir)
        os.rename(src, dst)
    else:
        raise ValueError(f"重命名 源文件不存在 {src}")


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

if __name__ == "__main__":

    # root = input('Please enter manga folder:')
    # if root == '':
    #     root = os.getcwd()
    #     print("未输入，使用当前目录: "+ root)
    # changePicName(folder)
    # optimizeNaming(folder)

    # 处理tachiyomi下载目录
    TEST_MODE = True
    if TEST_MODE:
        print("当前处于测试模式")

    tachiyomifolders = [
    ]

    dst = '/volume1/Media/TEST'
    for folder in tachiyomifolders:
        dirs = os.listdir(folder)
        for entry in dirs:
            full = os.path.join(folder, entry)
            if os.path.isdir(full):
                if entry == '@eaDir':
                    print("忽略群晖文件夹")
                    continue
                modified = tachiyomiManga(full, dst)
                print("开始压缩...")
                for key in modified.keys():
                    tachiyomiZip(key, modified.get(key))
                print("Done! \n")

    komgalibs = [
                ]
    for komgalib in komgalibs:
        komgaManga(komgalib)
        cleanFolderWithoutSuffix(komgalib, MANGA_TYPE)

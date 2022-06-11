#!/bin/python3
# -*- coding: utf-8 -*-
""" Optimize manga folder

解析tachiyomi下载的文件
优化文件名并压缩
转移到指定目录

含:批量重命名等方法

"""
import os
import re
import shutil
import zipfile


def finadAllFiles(root, escape_folder):
    """ return files under directory 'root'
    """
    for folder in escape_folder:
        if folder in root:
            return []
    total = []
    file_type = ['.zip', '.rar']
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


def changePicName(root):
    """ 更改 jpg 名称编号
    """
    dirs = os.listdir(root)
    start = 152
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
    处理tachiyomi下载目录下具体漫画:

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
            ch = str(ch)
            if ch.startswith('_第1話'):
                print("第一话 空格后跟随整个漫画名 需要特殊处理")
                oldpath = os.path.join(root, ch)
                newpath = os.path.join(dstfolder, manganame, '1')
                print(f"章节更新:  {ch} >>> 1 ")
                modifiedManga[oldpath] = newpath
            elif ' ' in ch:
                # 存在空格的 直接删除第一个之前内容
                oldpath = os.path.join(root, ch)
                newch = ch[ch.index(' '):].strip().replace(' - ', ' ')
                results = regexMatch(newch, '第[\d]*話')
                if results:
                    print("章节存在特殊情况 第xxx話")
                    num = results[0].strip('第話')
                    newch = newch.replace(results[0], num)
                # print(f"处理后 {newch}")
                newpath = os.path.join(dstfolder, manganame, newch)
                print(f"章节更新:  {ch} >>> {newch}")
                modifiedManga[oldpath] = newpath
            else:
                print("!!!!! 特殊章节")
                print(ch)
                print("!!!!!")
                raise
    print("\n")
    return modifiedManga


def tachiyomiZip(srcfolder, dest):
    """ 压缩源文件夹到目标文件
    """
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
    print(f"原始漫画名: {orignal}")
    name = replaceParentheses(orignal)
    replaces = ['个人汉化', 'DL版', '个人整理制作版', '禁漫掃圖組', '風的工房',
                '中國翻訳', '中国翻訳', 'C97', 'C96', '個人整合', '禁漫天堂']
    for r in replaces:
        name = name.replace(r, '')
    name = name.replace('[]', '').replace('()', '').strip()
    if name != orignal:
        print(f"更新漫画名: {orignal} >>> {name}")
    return name

if __name__ == "__main__":

    # root = input('Please enter manga folder:')
    # if root == '':
    #     root = os.getcwd()
    #     print("未输入，使用当前目录: "+ root)
    # changePicName(folder)
    # optimizeNaming(folder)

    # changeZipName(folder)

    # 处理tachiyomi下载目录
    root = 'tachiyomi下载目录'
    dst = '放压缩后文件的目录'
    dirs = os.listdir(root)
    for entry in dirs:
        full = os.path.join(root, entry)
        if os.path.isdir(full):
            if entry == '@eaDir':
                print("忽略群晖文件夹")
                continue
            modified = tachiyomiManga(full, dst)
            print("压缩漫画")
            for key in modified.keys():
                tachiyomiZip(key, modified.get(key))
            print("Done! \n")

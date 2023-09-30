
import os
import re
import shutil
import zipfile
from yaml import load  # pip install pyyaml

zip_type = ['.zip', '.cbz', '.pdf']

def loadConfig(configPath = ""):
    try:
        from yaml import CLoader as Loader
    except ImportError:
        from yaml import Loader

    if configPath == "":
        localPath = os.path.dirname(os.path.abspath(__file__))
        configPath = os.path.join(localPath, 'manga.yaml')
    data = None
    with open(configPath, mode="r", encoding="utf8") as c:
        data = load(c.read(), Loader=Loader)
    return data


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
            if entry.lower().endswith(tuple(zip_type)):
                # print("漫画目录已经是压缩文件")
                chapter = os.path.splitext(entry)[0]
                chapters.append(chapter)
    return chapters


def checkIfTankobonByChapter(chapters):
    # 区分单本,多章节,合集等
    isTankobon = False
    if len(chapters) == 0:
        print("未检测到章节")
        raise ValueError("未检测到章节")
    elif len(chapters) < 2:
        if chapters[0] == '_单章节' or chapters[0] == '单章节':
            # print("是单本漫画")
            isTankobon = True
        elif chapters[0] == '_Ch. 1' or chapters[0] == 'Ch. 1':
            print("可能是单本漫画,目前只有一个章节")
            isTankobon = True
    return isTankobon


def renamefile(src, dst):
    """ 移动文件
    """
    if src == dst:
        return
    if os.path.exists(src):
        dir = os.path.dirname(dst)
        if not os.path.exists(dir):
            os.makedirs(dir)
        shutil.move(src, dst)
    else:
        message = "重命名 源文件不存在 {0}".format(src)
        raise ValueError(message)


def zipfolder(srcfolder, destfile):
    """ 压缩 `srcfolder` 目录下的文件到 `destfile`
    :param srcfolder: 需要压缩的目录,仅压缩此目录下的文件,不会深层压缩
    """
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


def replaceParentheses(basestr: str):
    """ 替换特殊符号
    """
    basestr = basestr.replace('（', '(')
    basestr = basestr.replace('）', ')')
    basestr = basestr.replace('【', '[')
    basestr = basestr.replace('】', ']')
    return basestr


def regexMatch(basename, reg):
    """ 正则过滤
    """
    prog = re.compile(reg, re.IGNORECASE | re.X | re.S)
    result = prog.findall(basename)
    return result


def cleanFolderWithoutSuffix(folder, suffix):
    """ 删除无匹配后缀文件的目录
    """
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


def updateMangaName(orignal, groups, badtags):
    """ 更新漫画名
    """
    # print(f"原始漫画名: {orignal}")
    name = replaceParentheses(orignal)
    replaces = groups
    for r in replaces:
        name = name.replace(r, '')
    name = re.sub('C\d{2}', '', name, re.IGNORECASE)
    # 更改[]顺序
    results = regexMatch(name, '\[(.*?)\]')
    if results:
        retagname = name
        sorts = badtags
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


def fix_tankobon(manga_folder, name, chapters, groups, badtags, dst_folder):
    """ 修复单本漫画目录
    修正漫画名字, key为源文件, value为修复后文件地址
    """
    result = dict()
    manganame = updateMangaName(name, groups, badtags)
    sourcepath = os.path.join(manga_folder, chapters[0])
    dstpath = os.path.join(dst_folder, manganame, manganame)
    print(f"[-] 单本漫画整理:  {chapters[0]} >>> {manganame}")
    result[sourcepath] = dstpath
    return result


def fix_series(manga_folder, name, chapters, groups, badtags, dst_folder):
    """ 修复系列漫画目录
    修正漫画名字, key为源文件, value为修复后文件地址
    """
    result = dict()
    manganame = updateMangaName(name, groups, badtags)
    for ch in chapters:
        newch = updateChapter(ch)
        oldpath = os.path.join(manga_folder, ch)
        newpath = os.path.join(dst_folder, manganame, newch)
        result[oldpath] = newpath
    return result

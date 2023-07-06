
import os
import re
import shutil
import zipfile
from yaml import load  # pip install pyyaml


def loadConfig(configPath):
    try:
        from yaml import CLoader as Loader
    except ImportError:
        from yaml import Loader
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
    if os.path.exists(src):
        dir = os.path.dirname(dst)
        if not os.path.exists(dir):
            os.makedirs(dir)
        shutil.move(src, dst)
    else:
        raise ValueError(f"重命名 源文件不存在 {src}")


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


def regexMatch(basename, reg):
    """ 正则过滤
    """
    prog = re.compile(reg, re.IGNORECASE | re.X | re.S)
    result = prog.findall(basename)
    return result



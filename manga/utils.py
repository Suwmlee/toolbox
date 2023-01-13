
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

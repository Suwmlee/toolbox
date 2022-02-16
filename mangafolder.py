# -*- coding: utf-8 -*-
""" Optimize manga folder

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
    for i in basestr:
        if i in ['(', '【', '（']:
            basestr = basestr.replace(i, "[")
        if i in [')', '】', '）']:
            basestr = basestr.replace(i, "]")
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


def changeFolderName(root):
    """ 更改文件夹名字

    针对 Tachiyomi 下载的文件
    """
    dirs = os.listdir(root)
    for d in dirs:
        fullpath = os.path.join(root, d)
        if os.path.isdir(fullpath) and d.startswith("_第"):
            print(fullpath)
            temp = d.split(' ')
            newname = temp[1].strip('[]話')
            for i in range(len(temp)):
                if i == 2:
                    newname = newname + " - " + temp[2].strip('-')
                elif i > 2:
                    newname = newname + " " + temp[i].strip('-')
            # print(newname)
            newpath = os.path.join(root, newname)
            print(newpath)
            os.rename(fullpath, newpath)
        elif os.path.isdir(fullpath) and d.startswith("_单章节"):
            rootname = os.path.basename(root)
            newname = rootname
            newpath = os.path.join(root, newname)
            print(newpath)
            os.rename(fullpath, newpath)


def changeZipName(root):
    """ 更改压缩文件名字

    修正以前的命名
    """
    dirs = os.listdir(root)
    file_type = ['.zip', '.rar']
    filters = "过滤名"
    for d in dirs:
        fullpath = os.path.join(root, d)
        if os.path.splitext(fullpath)[1].lower() in file_type and d.startswith(filters):
            print(fullpath)
            name, ext = os.path.splitext(d)
            temp = name.split(' ')
            newname = temp[1].strip('[]話')
            for i in range(len(temp)):
                if i == 2:
                    newname = newname + " - " + temp[2].strip('-')
                elif i > 2:
                    newname = newname + " " + temp[i].strip('-')
            # print(newname)
            newpath = os.path.join(root, newname + ext)
            print(newpath)
            os.rename(fullpath, newpath)


def zipFolder(root):
    """ 压缩root目录下的文件夹

    压缩后的文件夹不会嵌套文件夹
    """
    # root = os.path.dirname(__file__)
    dirs = os.listdir(root)
    for d in dirs:
        fullpath = os.path.join(root, d)
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


if __name__ == "__main__":

    folder = input('Please enter manga folder:')
    # folder = 'E:\\Github\\seedbox\\test'
    if folder == '':
        folder = os.getcwd()
        print("未输入，使用当前目录: "+ folder)
    # changePicName(folder)
    # optimizeNaming(folder)

    changeZipName(folder)

    # Tachiyomi 漫画最顶层目录
    # 修改每个目录里的文件夹命名并压缩
    # dirs = os.listdir(folder)
    # for d in dirs:
    #     fullpath = os.path.join(folder, d)
    #     changeFolderName(fullpath)
    #     zipFolder(fullpath)

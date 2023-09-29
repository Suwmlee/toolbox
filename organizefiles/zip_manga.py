#!/bin/python
# -*- coding: utf-8 -*-
""" 
批量压缩漫画 jpg 文件
"""
import os
import zipfile

SRC_FOLDER = "/path/to/src"
DST_FOLDER = "/path/to/dst"
ZIP_LVL = 2
DRY_RUN = True

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


def deep_lvl_zip(root, lvl):
    """ 按层级压缩
    """
    dirs = os.listdir(root)
    for dd in dirs:
        full = os.path.join(root, dd)
        if os.path.isdir(full):
            if lvl == 1:
                filename = str(dd).replace("卷", "volume_") + ".zip"
                dstfile = os.path.join(DST_FOLDER, filename)
                print(f"{dd}  ===>  {dstfile}")
                if not DRY_RUN:
                    zipfolder(full, dstfile)
            else:
                newlvl = lvl - 1
                deep_lvl_zip(full, newlvl)


if __name__ == "__main__":
    DRY_RUN = True

    check = input('测试模式 (default:Yes):')
    if check.lower() == "n" or check.lower() == "no":
        DRY_RUN = False
    deep_lvl_zip(SRC_FOLDER, ZIP_LVL)


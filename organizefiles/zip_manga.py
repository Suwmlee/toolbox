
import os
import zipfile

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
    for dir in dirs:
        f = os.path.join(root, dir)
        if os.path.isdir(f):
            if lvl == 1:
                dstfile = f + ".zip"
                print(f"{dir}  ===>  {dstfile}")
            else:
                newlvl = lvl - 1
                deep_lvl_zip(f, newlvl)


if __name__ == "__main__":

    root = "/xx/xxx/xx"
    deep_lvl_zip(root, 2)


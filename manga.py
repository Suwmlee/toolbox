
import os
import re
from utils import loadConfig, regexMatch, renamefile, replaceParentheses, zipfolder

DEBUG_MODE = True


def moveTachiyomiManga(src, dst):
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
            modified = checkTachiyomiManga(full, dst)
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


def checkTachiyomiManga(root, dstfolder) -> dict:
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
        print("合集 暂不处理")
        # for ch in chapters:
        #     newch = updateChapter(ch)
        #     oldpath = os.path.join(root, ch)
        #     newpath = os.path.join(dstfolder, manganame, newch)
        #     modifiedManga[oldpath] = newpath
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

    if config['tachiyomi']['enable']:
        for tachi in config['tachiyomi']['mapping']:
            src = tachi['src']
            dst = tachi['dst']
            moveTachiyomiManga(src, dst)

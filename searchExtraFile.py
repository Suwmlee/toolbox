#!/bin/python
# -*- coding: utf-8 -*-
""" Optimize Movies folder

检测,删除影视目录额外文件
检测没有匹配视频的额外多余文件(例如 字幕,nfo,jpg等)
"""
import os
import shutil

video_type = ['.mp4', '.avi', '.rmvb', '.wmv',
              '.mov', '.mkv', '.flv', '.ts', '.webm', '.iso']
sub_type = ['.ass', '.srt', '.sub', '.ssa', '.smi', '.idx', '.sup',
            '.psb', '.usf', '.xss', '.ssf', '.rt', '.lrc', '.sbv', '.vtt', '.ttml']
ext_type = ['.png', '.jpg', '.bmp', '.nfo']


def checkFolderhasMedia(folder):
    """ 检测文件夹内是否有视频文件
    """
    if not os.path.isdir(folder):
        if os.path.exists(folder):
            return True
        return False
    for root, dirs, files in os.walk(folder, topdown=False):
        for file in files:
            if file.lower().endswith(tuple(video_type)) and not '.sample.' in file.lower():
                return True
    return False


def findfolderwithextrasubs(folder, suffix):
    """ 查找多余的字幕文件
    """
    sublist = []
    dirs = os.listdir(folder)
    for file in dirs:
        f = os.path.join(folder, file)
        if os.path.isdir(f):
            # print("文件夹内")
            subs = findfolderwithextrasubs(f, suffix)
            if subs:
                sublist.extend(subs)
        elif os.path.splitext(f)[1].lower() in suffix:
            # print("是字幕文件")
            dirname, basename = os.path.split(f)
            # basename = os.path.basename(f)
            # print(basename)
            basename2 = os.path.splitext(os.path.splitext(basename)[0])[0]
            # print(basename2)
            matchedVideo = False
            for vfile in dirs:
                if os.path.isdir(vfile):
                    continue
                elif os.path.splitext(vfile)[1].lower() in video_type and vfile.startswith(basename2):
                    # print("有匹配的视频文件: " + vfile)
                    matchedVideo = True
                    break
            if not matchedVideo:
                print("多余的字幕: " + f)
                sublist.append(f)
    return sublist


def findfolderwithextraext(folder, suffix):
    """ 查找多余的文件
    """
    extlist = []
    dirs = os.listdir(folder)
    for file in dirs:
        f = os.path.join(folder, file)
        if os.path.isdir(f):
            exts = findfolderwithextraext(f, suffix)
            if exts:
                extlist.extend(exts)
        elif os.path.splitext(f)[1].lower() in suffix:
            dirname, basename = os.path.split(f)
            basename2 = os.path.splitext(basename)[0]
            # TODO 检测不完全
            onlycheckV = False
            if basename2 == 'fanart' or basename2 == 'poster':
                onlycheckV = True
            elif '-fanart' in basename2 or '-poster' in basename2:
                basename2 = basename2[:-7]
            matchedVideo = False
            for vfile in dirs:
                if os.path.isdir(vfile):
                    continue
                elif os.path.splitext(vfile)[1].lower() in video_type:
                    if onlycheckV or basename2.lower() in os.path.basename(vfile).lower():
                        matchedVideo = True
                        break
            if not matchedVideo:
                print("多余的文件: " + f)
                extlist.append(f)
    return extlist


if __name__ == '__main__':

    #folder = input('Please input folder:')
    folder = '/volume1/Media/Movies'
    if folder == '':
        folder = os.getcwd()
        print("will use current folder: " + folder)

    print("extra subs:")
    subs = findfolderwithextrasubs(folder, sub_type)

    cleanSub = input('Clean all extra subs Yes/No (default:No):')
    if cleanSub.lower() == "y" or cleanSub.lower() == "yes":
        for sub in subs:
            os.remove(sub)
        print("Clean Subs Done")

    emptyFolders = []
    dirs = os.listdir(folder)
    for entry in dirs:
        full = os.path.join(folder, entry)
        if os.path.isdir(full):
            result = checkFolderhasMedia(full)
            if not result:
                print(f"{full} 文件夹内无视频文件")
                emptyFolders.append(full)
    cleanFolders = input('Clean all empty folders: Yes/No (default:No):')
    if cleanFolders.lower() == "y" or cleanFolders.lower() == "yes":
        for f in emptyFolders:
            shutil.rmtree(f)

    print("Done")

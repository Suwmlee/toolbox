#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
import os


video_type = ['.mp4', '.avi', '.rmvb', '.wmv',
              '.mov', '.mkv', '.flv', '.ts', '.webm', '.iso']
sub_type = ['.ass', '.srt', '.sub', '.ssa', '.smi', '.idx', '.sup',
            '.psb', '.usf', '.xss', '.ssf', '.rt', '.lrc', '.sbv', '.vtt', '.ttml']
ext_type = ['.png', '.jpg', '.bmp', '.nfo']


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

    folder = input('Please input folder:')
    # folder = 'E:\\Github\\seedbox\\test'
    if folder == '':
        folder = os.getcwd()
        print("will use current folder: " + folder)

    print("extra subs:")
    subs = findfolderwithextrasubs(folder, sub_type)

    # print("=======================================")
    # print("extra files:")
    # imgs = findfolderwithextraext(folder, ext_type)

    cleanSub = input('Clean all extra subs Yes/No (default:No):')
    if cleanSub.lower() == "y" or cleanSub.lower() == "yes":
        for sub in subs:
            os.remove(sub)
        print("Clean Subs Done")
    # cleanExtra = input('Clean all extra files Yes/No (default:No):')
    # if cleanExtra.lower() == "y" or cleanExtra.lower() == "yes":
    #     for img in imgs:
    #         os.remove(img)
    #     print("Clean Extra Done")
    print("Done")

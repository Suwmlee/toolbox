# -*- coding: utf-8 -*-

"""

更新 komga 内漫画的作者和星级


    流程：

        遍历漫画库内的漫画
        如果漫画没有星级
            按照目录 增加星级
        如果只有一个星级
            检测是否匹配当前目录星级
                不匹配  移动到匹配的目录
        如果有多个星级
            输出

        第一个 TAG 默认为作者
            无作者信息  增加作者

"""
import os
from komgaapi import KomgaApi
from utils import loadConfig, regexMatch, renamefile, cleanFolderWithoutSuffix


config = loadConfig()
MANGA_TYPE = config['manga-type']
libconfig = config['komgalib']

domain = libconfig['domain']
cookies = libconfig['cookies']
prefix_path = libconfig['prefix-path']
lib_path = libconfig['lib-path']

lib_names = libconfig['lib-names']
tier5 = libconfig['Tier5']
tier4 = libconfig['Tier4']
tier3 = libconfig['Tier3']



def move2lib(path, libroot, tier):
    """ 移动
    """
    abspath = path.replace('/data/', prefix_path)
    dest_root = lib_path + tier
    dest_path = path.replace(libroot, dest_root)
    print(f"[!] 移动 {abspath} ====> {dest_path}")
    renamefile(abspath, dest_path)


api = KomgaApi(domain, cookies)
libs = api.get_library()
if "error" in libs and libs["error"] == "Unauthorized":
    print("Unauthorized")
    exit()

for lib in libs:
    libname = lib['name']
    libroot = lib['root']
    if libname in lib_names:
        print(f"[!] 开始检测 {libname} ...")
        lib_lvl = 3
        if libname == tier4:
            lib_lvl = 4
        if libname == tier5:
            lib_lvl = 5

        lib_allseries = api.get_library_series(lib['id'])
        for series in lib_allseries:
            series_meta = api.get_series_book(series['id'])
            for chapter in series_meta:
                if chapter['deleted']:
                    continue
                changed = False
                # print(chapter['url']) # 章节的地址
                metadata = chapter['metadata']
                path = chapter['url']
                chapter_tags = metadata.setdefault('tags', [])

                tag_num = 0
                has_t3 = False
                has_t4 = False
                has_t5 = False
                if tier3 in chapter_tags:
                    tag_num = tag_num + 1
                    has_t3 = True
                if tier4 in chapter_tags:
                    tag_num = tag_num + 1
                    has_t4 = True
                if tier5 in chapter_tags:
                    tag_num = tag_num + 1
                    has_t5 = True
                if tag_num == 0:
                    # 没有星级 放心增加对应lvl
                    if lib_lvl == 4:
                        chapter_tags.append(tier4)
                        changed = True
                    if lib_lvl == 5:
                        chapter_tags.append(tier5)
                        changed = True
                elif tag_num == 1:
                    # 有一个星级，查看是否匹配，不匹配，则需要更改文件
                    if lib_lvl == 3 and not has_t3:
                        if has_t4:
                            move2lib(path, libroot, tier4)
                            continue
                        if has_t5:
                            move2lib(path, libroot, tier5)
                            continue
                    if lib_lvl == 4 and not has_t4:
                        if has_t3:
                            move2lib(path, libroot, tier3)
                            continue
                        if has_t5:
                            move2lib(path, libroot, tier5)
                            continue
                    if lib_lvl == 5 and not has_t5:
                        if has_t3:
                            move2lib(path, libroot, tier3)
                            continue
                        if has_t4:
                            move2lib(path, libroot, tier4)
                            continue
                else:
                    # 有多个星级，输出日志
                    print(f"[x] 有多个 TAG {chapter_tags} in 系列 {chapter['seriesTitle']}  //  {chapter['name']}")
                    print(f"[x] 有多个 TAG {chapter_tags} in 系列 {chapter['seriesTitle']}  //  {chapter['name']}")
                    continue

                # 使用 seriesTitle 获取作者信息, 章节获取更多 tag
                tags = regexMatch(chapter['seriesTitle'], '\[(.*?)\]')

                if len(tags) == 0:
                    print(f"[x] 无法解析出 TAG in {chapter['seriesTitle']}  //  {chapter['name']} ")
                    continue
                # add writer
                writer = tags[0]
                writer_meta = {"name": writer, "role": "writer"}
                if not writer_meta in metadata['authors']:
                    print(f"[-] 更新作者: {writer} in {chapter['seriesTitle']}  //  {chapter['name']}")
                    metadata.setdefault('authors', []).append(writer_meta)
                    changed = True

                if changed:
                    api.update_book_meta(chapter['id'], metadata)
                # else:
                #     print(f"[!] Pass {chapter['name']}")

                if lib_lvl > 3:
                    # 查看目录结构    lib / author / series / chapter.zip
                    mid = path.replace(libroot, '')
                    mids = os.path.normpath(mid).split(os.path.sep)
                    lvls = len(mids)
                    if lvls > 3 and mids[lvls-4] != '':
                        print(f"[!] 目录结构异常 {chapter['seriesTitle']}  //  {chapter['name']}")
                        raise
                    mangazip = mids[lvls-1] if lvls > 0 else None
                    mangafolder = mids[lvls-2] if lvls > 1 else None
                    authorfolder = mids[lvls-3] if lvls > 2 else None
                    if not authorfolder == writer:
                        authorfolder = writer
                    newpath = os.path.join(libroot, authorfolder, mangafolder, mangazip)
                    if newpath != path:
                        abspath = path.replace('/data/', prefix_path)
                        newpath = newpath.replace('/data/', prefix_path)
                        print(f"[!] 增加作者目录 {abspath} ====> {newpath}")
                        renamefile(abspath, newpath)

        libpath = libroot.replace('/data/', prefix_path)
        cleanFolderWithoutSuffix(libpath, MANGA_TYPE)

# 重新扫描所有库
for lib in libs:
    api.scan_lib(lib['id'])

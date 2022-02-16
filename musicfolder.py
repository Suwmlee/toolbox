# -*- coding: utf-8 -*-
""" Optimize music folder

Update SOX_LOCATION first!

requirements:
tinytag
"""
import os
import subprocess
from tinytag import TinyTag
import datetime


SOX_LOCATION = "E:\\Apps\\sox-14-4-2\\sox.exe"


def music_lists(root, escape_folder):
    """ return music files under directory 'root'
    """
    for folder in escape_folder:
        if folder in root:
            return []
    total = []
    file_type = ['.mp3', '.flac', '.ogg', '.opus', '.mp4', '.wma']
    dirs = os.listdir(root)
    for entry in dirs:
        f = os.path.join(root, entry)
        if os.path.isdir(f):
            total += music_lists(f, escape_folder)
        elif os.path.splitext(f)[1].lower() in file_type:
            total.append(f)
    return total


def genrate_tracklist(folder: str):
    """ genrate tracklist bbcode by TinyTag
    """
    print("genrate_tracklist start")
    musiclists = music_lists(folder, '')
    foldername = os.path.basename(folder)
    file = open(foldername+'.md', "w+", encoding='utf-8')
    top = "[b]Tracklist:[/b]"
    file.write(top + '\n\n')
    totalseconds = 0
    for single in musiclists:
        tag = TinyTag.get(single)
        # track
        tracknum = "%02d" % int(tag.track)
        # length
        seconds = round(tag.duration)
        totalseconds += seconds
        min, sec = divmod(seconds, 60)
        length = "%02d:%02d" % (min, sec)
        description = '[b]' + tracknum + '[/b]. ' + \
            tag.title + ' [i](' + length+')[/i]'
        file.write(description + '\n')

    # total length
    totallength = str(datetime.timedelta(seconds=totalseconds))
    file.write("\n[b]Total length:[/b] " + totallength)
    print("genrate_tracklist end")


def genrate_spectrogram(folder: str):
    """ genrate spectrogram by SOX
    command:  sox *.flac -n spectrogram -o Spectrogram.png
    """
    print("genrate_spectrogram start")
    command = '  *.flac -n spectrogram -o Spectrogram.png'
    subprocess.call(SOX_LOCATION + command, cwd=folder, shell=True)
    print("genrate_spectrogram end")


if __name__ == "__main__":

    folder = input('Please enter the music folder:')

    genrate_tracklist(folder)
    genrate_spectrogram(folder)

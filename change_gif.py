#!/bin/python3
# -*- coding: utf-8 -*-


import os
import shutil
from PIL import Image


def transparence2white(img):
    img=img.convert('RGBA') # 此步骤是将图像转为灰度(RGBA表示4x8位像素，带透明度掩模的真彩色；CMYK为4x8位像素，分色等)，可以省略
    sp = img.size
    width = sp[0]
    height = sp[1]
    for yh in range(height):
        for xw in range(width):
            dot = (xw, yh)
            color_d = img.getpixel(dot)  # 用getpixel方法来获取维度数据
            if(color_d[3] == 0):
                color_d = (255, 255, 255, 255)
                img.putpixel(dot, color_d)  # 赋值的方法是通过putpixel
    return img




if __name__ == "__main__":

    localPath = os.path.dirname(os.path.abspath(__file__))
    # srcfolder = os.path.join(localPath, 'emotion')
    # dstfolder = os.path.join(localPath, 'output')
    srcfolder = os.path.join(localPath, 'emotion2')
    dstfolder = os.path.join(localPath, 'output2')

    if os.path.exists(dstfolder):
        shutil.rmtree(dstfolder)
        os.makedirs(dstfolder)
    else:
        os.makedirs(dstfolder)

    emots = os.listdir(srcfolder)

    for em in emots:
        path = os.path.join(srcfolder, em)
        

        img = Image.open(path)

        img = transparence2white(img)
        # # img.show() # 显示图片

        if em.endswith('png'):
            em = em.replace('png', 'gif')
        savepath = os.path.join(dstfolder, em)

        img.save(savepath)  # 保存图片

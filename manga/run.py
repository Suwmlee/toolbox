#!/bin/python3
# -*- coding: utf-8 -*-


import argparse
from transfer_manga import transfer_manga
from organize_manga import start_organize
from organize_komga import organize_komga_manga
from utils import loadConfig


if __name__ == "__main__":
    config = loadConfig()

    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--test', action='store_true', help='测试模式')
    parser.add_argument('-f', '--force', action='store_true', help='强制执行变更')
    parser.add_argument('-tf', '--transfer', action='store_true', help='tachiyomi转移到komga')
    parser.add_argument('-og', '--organize', action='store_true', help='整理manga')
    parser.add_argument('-kg', '--komga', action='store_true', help='根据komga进行整理')
    args = parser.parse_args()

    if args.test:
        TEST_MODE = True
    else:
        TEST_MODE = config['dry-run']
    if args.force:
        TEST_MODE = False

    if args.transfer:
        transfer_manga(config)
    
    if args.organize:
        start_organize(config)

    if args.komga:
        organize_komga_manga(config)


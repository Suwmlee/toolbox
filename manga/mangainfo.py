
import os
from utils import findMangaChapter, checkIfTankobonByChapter


class MangaInfo():

    def __init__(self, root: str):
        self.isManga = True
        self.fullPath = root
        self.name = os.path.basename(root)
        self.chapters = findMangaChapter(root)
        # 检测单本，多本
        if len(self.chapters) < 1:
            print("[x] 无章节")
            self.isManga = False
            return
        if checkIfTankobonByChapter(self.chapters):
            self.isTankobon = True
            self.isSeries = False
        else:
            self.isTankobon = False
            self.isSeries = True

    def initExtra(self):
        self.typeName = None
        self.ended = False

        self.keepTag = True
        self.dstFolder = ''

    def analysisManga(self, config):
        self.initExtra()
        self.analysisMangaType(config)
        self.queryMangaMapping(config)

    def analysisMangaType(self, config):
        """ 
        type: name, folder, tankobon, series
        """
        # 从上往下依次判断
        for filter in config['filters']:
            if 'ended' in filter and self.name in filter['ended']:
                self.ended = True
                self.typeName = filter['name']
                break
            if filter['type'] == 'name':
                if self.name in filter['names']:
                    self.typeName = filter['name']
            elif filter['type'] == 'folder':
                for folder in filter['folders']:
                    if self.fullPath.startswith(folder):
                        self.typeName = filter['name']
                        break
            elif filter['type'] == 'tankobon':
                if self.isTankobon:
                    self.typeName = filter['name']
            elif filter['type'] == 'series':
                if self.isSeries:
                    self.typeName = filter['name']
            if self.typeName:
                break

    def queryMangaMapping(self, config):
        """ 查询漫画映射
        """
        for map in config['mapping']:
            if map['name'] == self.typeName:
                if self.ended:
                    flag = map['ended']
                else:
                    flag = map['default']
                if flag == 'move':
                    self.dstFolder = map['dst']
                    self.keepTag = False
                break

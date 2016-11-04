# -*- coding:utf8 -*-


import xml.dom.minidom
import os
import Image
import shutil
# from PIL import Image

class txtTransToxml():
    def __init__(self, imgfolderpath, sourceTxtPath, objXmlFolderPath,
                 Tag_foldername='VOC2007', owner='David Webb', clear_flag=False):
        self.imgfp = imgfolderpath              # 存放所有图片的目录
        self.sTP = sourceTxtPath                # 存放标记数据信息的文本文件
        self.objXFP = objXmlFolderPath          # 存放生成的xml文件的目录
        self.tag_foldername = Tag_foldername    # xml文件中"foldername"标签的值
        self.owner = owner
        self.clear_flag = clear_flag
        pass

    def appendchildnode(self, doc, fathernode, childnodelist):
        """ 为指定节点添加子节点 """
        if isinstance(childnodelist, list):
            for child in childnodelist:
                tmpnode = doc.createElement(child[0])
                tmpnode.appendChild(doc.createTextNode(child[1]))
                fathernode.appendChild(tmpnode)
            return fathernode
        else:
            print 'childnode参数错误！'
            return False
        pass

    def createObjectnode(self, doc, taginfolist):
        """ 创建新的object节点 , 并返回节点 """
        objectnode = doc.createElement('object')
        objectnode = self.appendchildnode(doc, objectnode, [('name', taginfolist[1],), ('pose', 'Unspecified',),
                                                            ('truncated', '0',), ('difficult', '0',)])
        bndboxnode = doc.createElement('bndbox')
        bndboxnode = self.appendchildnode(doc, bndboxnode, [('xmin', taginfolist[2],), ('ymin', taginfolist[3],), ('xmax', taginfolist[4],), ('ymax',taginfolist[5],)])
        objectnode.appendChild(bndboxnode)
        return objectnode
        pass

    def createNewXml(self, taginfolist, imSize):
        '''
         参数：
            taginfolist = [图片名, 标记, xmin, ymin, xmax, ymax]
            imSize      = [width, height, depth]
        '''
        doc = xml.dom.minidom.Document()
        # 创建一个根节点Managers对象
        root = doc.createElement('annotation')
        doc.appendChild(root)

        foldernode = doc.createElement('folder')
        foldernode.appendChild(doc.createTextNode(self.tag_foldername))
        root.appendChild(foldernode)

        filenamenode = doc.createElement('filename')
        filenamenode.appendChild(doc.createTextNode(taginfolist[0]))
        root.appendChild(filenamenode)

        sourcenode = doc.createElement('source')
        sourcenode = self.appendchildnode(doc, sourcenode, [('database', 'My Database',), ('annotation', 'VOC2007',),
                                                            ('image', 'flickr',), ('flickrid', 'NULL',)])
        root.appendChild(sourcenode)

        ownernode = doc.createElement('owner')
        ownernode = self.appendchildnode(doc, ownernode, [('flickrid', 'NULL',), ('name', self.owner,)])
        root.appendChild(ownernode)

        sizenode = doc.createElement('size')
        sizenode = self.appendchildnode(doc, sizenode, [('width', str(imSize[0]),), ('height', str(imSize[1]),), ('depth', str(imSize[2]),)])
        root.appendChild(sizenode)

        segmentednode = doc.createElement('segmented')
        segmentednode.appendChild(doc.createTextNode('0'))
        root.appendChild(segmentednode)

        objectnode = self.createObjectnode(doc, taginfolist)
        root.appendChild(objectnode)

        fp = open(os.path.join(self.objXFP, taginfolist[0].split('.')[0] + '.xml'), 'w')
        # doc.writexml(fp, indent='\t', addindent='\t', newl='\n', encoding="utf-8")
        doc.writexml(fp)
        fp.close()
        pass

    def isXmlexisted(self, imgname):
        """检测图片对应的xml文件是否存在"""
        tmpname = imgname.split('.')[0] + '.xml'
        return tmpname in self.getfilenames(self.objXFP)
        pass

    def getfilenames(self, foldPath):
        """ 获得指定目录下的所有文件的名称 """
        if os.path.isdir(foldPath):
            return os.listdir(foldPath)
        else:
            print "查询目录下文件：路径输入有误！"
            return False
        pass

    def getImgSize(self, imgpath):
        ''' 获取图片的信息：长\宽\深度 '''
        mode_to_bpp = {'1': 1, 'L': 8, 'P': 8, 'RGB': 24, 'RGBA': 32, 'CMYK': 32, 'YCbCr': 24, 'I': 32, 'F': 32}
        im = Image.open(imgpath)
        sizelist = list(im.size)
        sizelist.append(mode_to_bpp[im.mode])
        return sizelist
        pass

    def removeXFP(self):
        """ 清空xml存放的文件加下的所有文件 """
        print "清空已有的xml文件......"
        shutil.rmtree(self.objXFP)
        os.mkdir(self.objXFP)
        print '清空完成！'
        pass

    def preetyXmls(self):
        """ 将xml格式化输出 """
        for file in os.listdir(self.objXFP):
            fileName = os.path.join(self.objXFP, file)
            with open(fileName, 'r') as rw:
                # tmptxt = rw.read().replace('\t', '').replace('\n', '')
                tmptxt = rw.read()
                newxml = xml.dom.minidom.parseString(tmptxt)
                newxml = newxml.toprettyxml().strip()
                # print newfp
            with open(fileName, 'w') as wr:
                wr.write(newxml)
            # doc = xml.dom.minidom.parse(os.path.join(self.objXFP, file))
            # print doc.toxml()
        pass


    def run(self):

        # 先清空xml文件夹
        if self.clear_flag:
            self.removeXFP()

        # 读取txt文件中的标记数据
        with open(self.sTP, 'r') as rd:
            datalines = rd.readlines()

        # 生成xml文件
        for line in datalines:
            taginfolist = line.split()  # taginfolist = [图片名, 标记, xmin, ymin, xmax, ymax]
            if self.isXmlexisted(taginfolist[0]):   # xml文件已经存在
                doc = xml.dom.minidom.parse(os.path.join(self.objXFP, taginfolist[0].split('.')[0] + '.xml'))
                root = doc.documentElement
                objectnode = self.createObjectnode(doc, taginfolist)
                root.appendChild(objectnode)
                with open(os.path.join(self.objXFP, taginfolist[0].split('.')[0] + '.xml'), 'wb') as fp:
                    doc.writexml(fp)
            else:                                   # xml文件不存在,新建xml
                imSize = self.getImgSize(os.path.join(self.imgfp, taginfolist[0]))
                self.createNewXml(taginfolist, imSize)

        # 格式化输出
        self.preetyXmls()
        pass

if __name__ == '__main__':
    print "警告：程序'clear_flag'参数可以设置转换前清空xml存放目录下的文件，请注意！"
    tmpinstance = txtTransToxml('./VOC2007xml/img', './VOC2007xml/img/output.txt', './VOC2007xml/JPEGImages', clear_flag=True)
    tmpinstance.run()            



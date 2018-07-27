# -*- coding:utf8 -*-


import xml.dom.minidom
import os
import Image
import shutil
import json
import cv2
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

    def tagjson2txt(self, jsonfile, txtfile="captcha_6_tag_15w_noline.txt"):
        """ 讲保存tag和box信息的json文件转换成txt文件, 每行信息：（图片名, 标记, xmin, ymin, xmax, ymax）,其中不需要逗号隔开,用空格 """

        with open(jsonfile, "r")as rd:
            tagdic = json.loads(rd.read())
        fp = open(txtfile, 'a')

        for k, v in tagdic.items():
            boxlist = v["boxlist"]
            taglist = list(v["label"])
            for tag, box in zip(taglist, boxlist):
                tmp_anstrlist = []
                tmp_anstrlist.append(("%09d" % int(k)) + '.jpg')
                tmp_anstrlist.append(tag)
                tmp_anstrlist.extend([str(b) for b in box])
                print tmp_anstrlist
                fp.write(" ".join(tmp_anstrlist).strip() + "\n")
                pass
        fp.close()


    def checkright(self):
        """ 检查标记数据中是否有不合格的数据 """
        def rangeDetec(box):
            r1 = box[0] < 0 or box[0] > 139 or box[2] < 0 or box[2] > 139
            r2 = box[1] < 0 or box[1] > 43 or box[3] < 0 or box[3] > 43

            if r1 or r2:
                return False
            return True

        countDic = {
            '0':0,'1':0,'2':0,'3':0,'4':0,'5':0,'6':0,'7':0,'8':0,'9':0,'a':0,'b':0,'c':0,'d':0,
            'e':0,'f':0,'g':0,'h':0,'i':0,'j':0,'k':0,'l':0,'m':0,'n':0,'o':0,'p':0,'q':0,'r':0,
            's':0,'t':0,'u':0,'v':0,'w':0,'x':0,'y':0,'z':0,'A':0,'B':0,'C':0,'D':0,'E':0,'F':0,
            'G':0,'H':0,'I':0,'J':0,'K':0,'L':0,'M':0,'N':0,'O':0,'P':0,'Q':0,'R':0,'S':0,'T':0,
            'U':0,'V':0,'W':0,'X':0,'Y':0,'Z':0
        }
        with open("captcha_1-char_label.json", "r")as rd:
            labeldic = json.loads(rd.read())
        for k, v in labeldic.items():
            boxlist = v["boxlist"]
            taglist = list(v["label"])
            for t in taglist:
                countDic[t] += 1
            if len(boxlist) != len(taglist):
                print len(boxlist), len(taglist)
                print k
                continue
            for box in boxlist:
                if rangeDetec(box):
                    print k
                    break
        for k, v in countDic.items():
            if v == 0:
                print k
        print countDic
        pass


    def checkimgright(self):
        """ 检测是否验证码图片尺寸有问题：裁剪粘贴导致边缘不整齐 """
        imagesdirpath = "/home/jingdata/Document/LAB_CODE/caffe_fasterrcnn_origindata/captcha_1-char/"
        imglist = os.listdir(imagesdirpath)
        for img in imglist:
            imgobj = cv2.imread(os.path.join(imagesdirpath, img),  0)
            imshape = imgobj.shape
            if imshape != (44, 140):
                print img

        pass

    def freshtagjson(self, jsonfile):
        """
            由于box的ymin设置为0 ，而fasterrcnn训练时会将xmin,ymin,xmax,ymax都减1，导致训练报错
                RuntimeWarning: invalid value encountered in greater_equal
                keep = np.where((ws >= min_size) & (hs >= min_size))[0]
            所以需要更新tagjson讲xmin=0, ymin =0 改为 2
        """
        with open(jsonfile, "r")as rd:
            tagdic = json.loads(rd.read())
        for k, v in tagdic.items():
            boxlist = v["boxlist"]
            # taglist = list(v["label"])
	    v["label"] = v["label"].lower()
            for box in boxlist:
                if box[0] == 0:
                    box[0] = 2
                if box[1] == 0:
                    box[1] = 2
        with open(jsonfile, "w")as wr:
            wr.write(json.dumps(tagdic))
        pass
	
    def lowerjsonlabel(self):
	
	pass

    def run(self):

        # 先清空xml文件夹
        if self.clear_flag:
            self.removeXFP()

        # 读取txt文件中的标记数据
        with open(self.sTP, 'r') as rd:
            datalines = rd.readlines()

        # 生成xml文件
        for c, line in enumerate(datalines):
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
            if c % 1000 ==0 and c:
                print "解析了%s行信息......" % c
        # 格式化输出
        self.preetyXmls()
        pass

if __name__ == '__main__':
    print "警告：程序'clear_flag'参数可以设置转换前清空xml存放目录下的文件，请注意！"
    # tmpinstance = txtTransToxml('./VOC2007xml/img', './VOC2007xml/img/output.txt', './VOC2007xml/JPEGImages', clear_flag=True)
    imagesdirpath = "/home/jingdata/Document/LAB_CODE/caffe_fasterrcnn_origindata/mkdataset/Faster-Rcnn/captcha_6-char_test_15w_withoutline/"
    tmpinstance = txtTransToxml(imagesdirpath, './captcha_6_tag_15w_noline.txt', './captchaXMLs', clear_flag=True)
    # tmpinstance.freshtagjson("/home/jingdata/Document/LAB_CODE/caffe_fasterrcnn_origindata/mkdataset/Faster-Rcnn/captcha_6-char_test_15w_label.json")
    # tmpinstance.tagjson2txt("/home/jingdata/Document/LAB_CODE/caffe_fasterrcnn_origindata/mkdataset/Faster-Rcnn/captcha_6-char_test_15w_label.json", txtfile="captcha_6_tag_15w_noline.txt")
    tmpinstance.run()
    # tmpinstance.checkright()
    # tmpinstance.checkimgright()
    # with open("captcha_1_tag.txt", "r")as rd:
    #     lines = rd.readlines()
    # print len(lines)


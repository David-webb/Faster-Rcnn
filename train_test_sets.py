#!/usr/bin/env python
# -*- coding:utf-8 -*-
__author__ = 'Tengwei'

import os
import random

def savefile(txtSavedPath, fileName, answerList):
    finalstr = ''
    for i in answerList[:-1]:
        finalstr += (i + '\n')
    finalstr += answerList[-1]
    with open(os.path.join(txtSavedPath, fileName), 'w') as wr:
        wr.write(finalstr)
    pass

def makeTrainTestSets(anwserSavedPath, xmlfilespath, trainval_percent, train_percent):
    """
        功能：
            将已有的标记样本按照指定的比例分成训练样本、 测试样本、验证样本以及测试_验证样本,
            分别保存为train.txt\test.txt\val.txt\trainval.txt
        参数：
            trainval_percent: 测试数据和验证数据总共占的比例
            train_percent: 训练数据占的比例
    """
    # 获得所有的xml文件名（去除后缀）
    xmllist = os.listdir(xmlfilespath)
    xmllist = [x.split('.')[0] for x in xmllist]

    # 对上述list进行排序
    # xmllist.sort(key=(lambda x: int(x))) # 对xml文件进行排序

    # 开始划分各种集合
    xmllen = len(xmllist)
    trainvalList = random.sample(xmllist, int(xmllen*trainval_percent))     # trainval集合
    savefile(anwserSavedPath, 'trainval.txt', trainvalList)

    trainlist = random.sample(trainvalList, int(len(trainvalList)*train_percent))   # train集合
    savefile(anwserSavedPath, 'train.txt', trainlist)

    vallist = [x for x in trainvalList if x not in trainlist]               # val的集合
    savefile(anwserSavedPath, 'val.txt', vallist)

    # testlist = [x for x in xmllist if x not in trainvalList]              # test 集合
    testlist = list(set(xmllist) ^ set(trainvalList))
    savefile(anwserSavedPath, 'test.txt', testlist)
    # print trainvalList, testlist

    pass


if __name__ == '__main__':
    # makeTrainTestSets('.', 'VOC2007xml/JPEGImages', 0.5, 0.5)
    makeTrainTestSets('./train_test_set', './captchaXMLs', 0.8, 0.2)
    pass

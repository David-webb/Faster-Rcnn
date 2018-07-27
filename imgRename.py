# -*- coding:utf8 -*-

import os

def rename(dirpath):
    path = dirpath
    filelist = os.listdir(path)                     # 该文件夹下所有的文件（包括文件夹）
    try:  # (第二次改名的话,一定要排序，因为os.listdir生成的元素是随机的，第二次改名(os.rename函数)会将第一生成的同名文件覆盖，导致总文件数目变少)
        filelist.sort(key=lambda x: int(x[:-4]))
        print "文件有序"
        # return True
    except:
        print "第一次排序"

    for count, files in enumerate(filelist, 1):     # 遍历所有文件
        # print count, files
        Olddir = os.path.join(path, files)          # 原来的文件路径
        if os.path.isdir(Olddir):                   # 如果是文件夹则跳过
            continue
        filename = os.path.splitext(files)[0]       # 文件名
        filetype = os.path.splitext(files)[1]       # 文件扩展名
        # Newdir = os.path.join(path, ("%09d" % count) + filetype)   # 新的文件路径
        Newdir = os.path.join(path, ("%09d" % int(filename)) + '.jpg')  # 新的文件路径
        print count, files, Newdir
        os.rename(Olddir, Newdir)                   # 重命名
    return True

if __name__ == "__main__":
#     for i in os.listdir('./image/car'):
#         # print i
#         tmpdir = os.path.join("./image/car/", i)
#         if not os.path.isdir(tmpdir):  # 如果是文件则跳过
#             continue
#         rename(tmpdir)
#
     #objdir = "/home/jingdata/Document/LAB_CODE/caffe_fasterrcnn_origindata/mkdataset/Faster-Rcnn/captcha_1-char_12w/"
     
     objdir = "/home/jingdata/Document/LAB_CODE/caffe_fasterrcnn_origindata/mkdataset/Faster-Rcnn/captcha_6-char_test_15w_withoutline"
     rename(objdir)

#    a = [str(i) for i in range(10)]
#    a.extend([chr(i) for i in range(97, 123)])
#    a.extend([chr(i) for i in range(65, 91)])
#    print ",".join(["'%s'"% c for c in a])

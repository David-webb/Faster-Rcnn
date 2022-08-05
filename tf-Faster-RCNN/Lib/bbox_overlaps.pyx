# -*- coding: utf-8 -*-
"""
Created on Sun Jan  1 20:25:19 2017

@author: Kevin Liang (modification)

Calculates bounding box overlaps between N bounding boxes, and K query boxes 
(anchors) and return a matrix of overlap proportions

Written in Cython for optimization.
"""
# --------------------------------------------------------
# Fast R-CNN
# Copyright (c) 2015 Microsoft
# Licensed under The MIT License [see LICENSE for details]
# Written by Sergey Karayev
# --------------------------------------------------------

cimport cython
import numpy as np
cimport numpy as np

DTYPE = np.float
ctypedef np.float_t DTYPE_t

def bbox_overlaps(
        np.ndarray[DTYPE_t, ndim=2] boxes,
        np.ndarray[DTYPE_t, ndim=2] query_boxes):
    """
    Parameters
    ----------
    boxes: (N, 4) ndarray of float: anchors
    query_boxes: (K, 4) ndarray of float: GT_boxes
    Returns
    -------
    overlaps: (N, K) ndarray of overlap between boxes and query_boxes
    """
    cdef unsigned int N = boxes.shape[0]
    cdef unsigned int K = query_boxes.shape[0]
    cdef np.ndarray[DTYPE_t, ndim=2] overlaps = np.zeros((N, K), dtype=DTYPE)
    cdef DTYPE_t iw, ih, box_area
    cdef DTYPE_t ua
    cdef unsigned int k, n
    for k in range(K):
        box_area = (      # 当前GT_box的面积                          # 这里为什么要加1 ？？？？
            (query_boxes[k, 2] - query_boxes[k, 0] + 1) *       
            (query_boxes[k, 3] - query_boxes[k, 1] + 1)
        )
        for n in range(N):
            iw = (      # 判断anchor 和 DT_box 在x轴方向有无交集
                min(boxes[n, 2], query_boxes[k, 2]) -
                max(boxes[n, 0], query_boxes[k, 0]) + 1         # 这里为什么要加1 ？？？？
            )
            if iw > 0:
                ih = (      # 在x轴有交集的情况下，判断anchor 和 DT_box 在y轴方向有无交集
                    min(boxes[n, 3], query_boxes[k, 3]) -
                    max(boxes[n, 1], query_boxes[k, 1]) + 1     # 这里为什么要加1 ？？？？
                )
                if ih > 0:
                    ua = float(             # 并集面积 = anchor_S + GT_box_S - 交集面积
                        (boxes[n, 2] - boxes[n, 0] + 1) *
                        (boxes[n, 3] - boxes[n, 1] + 1) +
                        box_area - iw * ih
                    )
                    overlaps[n, k] = iw * ih / ua
    return overlaps

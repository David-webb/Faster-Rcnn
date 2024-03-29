# -*- coding: utf-8 -*-
"""
Created on Sun Jan  1 16:11:17 2017

@author: Kevin Liang (modifications)

Anchor Target Layer: Creates all the anchors in the final convolutional feature
map, assigns anchors to ground truth boxes, and applies labels of "objectness"

Adapted from the official Faster R-CNN repo: 
https://github.com/rbgirshick/py-faster-rcnn/blob/master/lib/rpn/anchor_target_layer.py
"""

# --------------------------------------------------------
# Faster R-CNN
# Copyright (c) 2015 Microsoft
# Licensed under The MIT License [see LICENSE for details]
# Written by Ross Girshick and Sean Bell
# --------------------------------------------------------

import sys
sys.path.append('../')

import numpy as np
import numpy.random as npr
import tensorflow as tf

from Lib.bbox_overlaps import bbox_overlaps
from Lib.bbox_transform import bbox_transform
from Lib.faster_rcnn_config import cfg
from Lib.generate_anchors import generate_anchors


def anchor_target_layer(rpn_cls_score, gt_boxes, im_dims, _feat_stride, anchor_scales):
    '''
    Make Python version of _anchor_target_layer_py below Tensorflow compatible
    '''
    rpn_labels,rpn_bbox_targets,rpn_bbox_inside_weights,rpn_bbox_outside_weights = \
        tf.py_func(_anchor_target_layer_py, [rpn_cls_score, gt_boxes, im_dims, _feat_stride, anchor_scales],
                   [tf.float32, tf.float32, tf.float32, tf.float32])

    rpn_labels = tf.convert_to_tensor(tf.cast(rpn_labels,tf.int32), name = 'rpn_labels')
    rpn_bbox_targets = tf.convert_to_tensor(rpn_bbox_targets, name = 'rpn_bbox_targets')
    rpn_bbox_inside_weights = tf.convert_to_tensor(rpn_bbox_inside_weights , name = 'rpn_bbox_inside_weights')
    rpn_bbox_outside_weights = tf.convert_to_tensor(rpn_bbox_outside_weights , name = 'rpn_bbox_outside_weights')

    return rpn_labels, rpn_bbox_targets, rpn_bbox_inside_weights, rpn_bbox_outside_weights


def _anchor_target_layer_py(rpn_cls_score, gt_boxes, im_dims, _feat_stride, anchor_scales):
    """
        Python version    
        
        Assign anchors to ground-truth targets. Produces anchor classification
        labels and bounding-box regression targets.
        
        # Algorithm:
        #
        # for each (H, W) location i
        #   generate 9 anchor boxes centered on cell i
        #   apply predicted bbox deltas at cell i to each of the 9 anchors
        # filter out-of-image anchors
        # measure GT overlap
    """
    im_dims = im_dims[0]
    _anchors = generate_anchors(scales=np.array(anchor_scales)) # featureMap中一个点的k个anchor
    _num_anchors = _anchors.shape[0]
    
    # allow boxes to sit over the edge by a small amount
    _allowed_border =  0
    
    # Only minibatch of 1 supported
    assert rpn_cls_score.shape[0] == 1, \
        'Only single item batches are supported'    
    
    # map of shape (..., H, W)
    # 特征图的height和weight
    height, width = rpn_cls_score.shape[1:3]
    
    # 1. Generate proposals from bbox deltas and shifted anchors
    # 构建视野图：
    # 这里乘以了_feat_stride, 等同于将原图按照特征图每个像素点对应的视野进行划分，视野与视野之间没有overlap
    shift_x = np.arange(0, width) * _feat_stride
    shift_y = np.arange(0, height) * _feat_stride
    shift_x, shift_y = np.meshgrid(shift_x, shift_y)
    shifts = np.vstack((shift_x.ravel(), shift_y.ravel(),
                        shift_x.ravel(), shift_y.ravel())).transpose()  # shape[height*width, 4], 
     
    # add A anchors (1, A, 4) to
    # cell K shifts (K, 1, 4) to get
    # shift anchors (K, A, 4)
    # reshape to (K*A, 4) shifted anchors
    A = _num_anchors
    K = shifts.shape[0]
    all_anchors = (_anchors.reshape((1, A, 4)) +
                   shifts.reshape((1, K, 4)).transpose((1, 0, 2)))      # 这样广播的做法，相当于将anchors模版在特征图上逐点滑动，等价于视野图上逐个视野滑动
    all_anchors = all_anchors.reshape((K * A, 4))
    total_anchors = int(K * A)
    #print("all_anchors:", all_anchors) 
    # anchors inside the image
    #print("im_dims:", im_dims)
    inds_inside = np.where(
        (all_anchors[:, 0] >= -_allowed_border) &
        (all_anchors[:, 1] >= -_allowed_border) &
        (all_anchors[:, 2] < im_dims[1] + _allowed_border) &  # width
        (all_anchors[:, 3] < im_dims[0] + _allowed_border)    # height
    )[0]
    #print("inds_inside", inds_inside) 
    # keep only inside anchors
    anchors = all_anchors[inds_inside, :]
    
    # label: 1 is positive, 0 is negative, -1 is dont care
    labels = np.empty((len(inds_inside), ), dtype=np.float32)
    labels.fill(-1)
    
    # Iou计算
    # overlaps between the anchors and the gt boxes
    # overlaps (ex, gt)
    # overlaps 是二维数组，行号是anchors， 列是GT_box, 元素是IOU值
    overlaps = bbox_overlaps(
        np.ascontiguousarray(anchors, dtype=np.float),
        np.ascontiguousarray(gt_boxes, dtype=np.float))

    #print("overlaps", overlaps)
    argmax_overlaps = overlaps.argmax(axis=1)# 每个anchor的交集最大的GT_box的索引
    max_overlaps = overlaps[np.arange(len(inds_inside)), argmax_overlaps]       # 
    gt_argmax_overlaps = overlaps.argmax(axis=0) # 每个GT_box交集最大的anchor
    gt_max_overlaps = overlaps[gt_argmax_overlaps,  
                               np.arange(overlaps.shape[1])]
    gt_argmax_overlaps = np.where(overlaps == gt_max_overlaps)[0]  # 每个GT_box交集最大的anchor的索引
    
    if not cfg.TRAIN.RPN_CLOBBER_POSITIVES:
        # assign bg labels first so that positive labels can clobber them
        # 先设置negative anchors, 这样后面有特殊情况的positive anchors，也可以进行覆盖
        labels[max_overlaps < cfg.TRAIN.RPN_NEGATIVE_OVERLAP] = 0

    # fg label: for each gt, anchor with highest overlap
    labels[gt_argmax_overlaps] = 1

    # fg label: above threshold IOU
    labels[max_overlaps >= cfg.TRAIN.RPN_POSITIVE_OVERLAP] = 1

    if cfg.TRAIN.RPN_CLOBBER_POSITIVES:
        # assign bg labels last so that negative labels can clobber positives
        # 后设置negative anchors
        labels[max_overlaps < cfg.TRAIN.RPN_NEGATIVE_OVERLAP] = 0

    # subsample positive labels if we have too many
    num_fg = int(cfg.TRAIN.RPN_FG_FRACTION * cfg.TRAIN.RPN_BATCHSIZE)
    fg_inds = np.where(labels == 1)[0]
    if len(fg_inds) > num_fg:
        disable_inds = npr.choice(
            fg_inds, size=(len(fg_inds) - num_fg), replace=False)
        labels[disable_inds] = -1

    # subsample negative labels if we have too many
    num_bg = cfg.TRAIN.RPN_BATCHSIZE - np.sum(labels == 1)
    bg_inds = np.where(labels == 0)[0]
    if len(bg_inds) > num_bg:
        disable_inds = npr.choice(
            bg_inds, size=(len(bg_inds) - num_bg), replace=False)
        labels[disable_inds] = -1

    # bbox_targets: The deltas (relative to anchors) that Faster R-CNN should 
    # try to predict at each anchor
    # TODO: This "weights" business might be deprecated. Requires investigation
    bbox_targets = np.zeros((len(inds_inside), 4), dtype=np.float32)
    bbox_targets = _compute_targets(anchors, gt_boxes[argmax_overlaps, :])  # anchors 是所有在框内的boxes, gt_boxes是所有的GT_boxes, argmax_overlaps是每个anchor交集最大的GT_box的索引 # 返回的是每个anchor对应的回归系数:dx,dy,dw,dh

    bbox_inside_weights = np.zeros((len(inds_inside), 4), dtype=np.float32)
    bbox_inside_weights[labels == 1, :] = np.array(cfg.TRAIN.RPN_BBOX_INSIDE_WEIGHTS)   # 所有的正样本的权重都为1

    bbox_outside_weights = np.zeros((len(inds_inside), 4), dtype=np.float32)
    if cfg.TRAIN.RPN_POSITIVE_WEIGHT < 0:       # 统一的权重
        # uniform weighting of examples (given non-uniform sampling)
        num_examples = np.sum(labels >= 0)
        positive_weights = np.ones((1, 4)) * 1.0 / num_examples
        negative_weights = np.ones((1, 4)) * 1.0 / num_examples
    else:                                       # pos/neg 分别计算权重
        assert ((cfg.TRAIN.RPN_POSITIVE_WEIGHT > 0) &
                (cfg.TRAIN.RPN_POSITIVE_WEIGHT < 1))
        positive_weights = (cfg.TRAIN.RPN_POSITIVE_WEIGHT /
                            np.sum(labels == 1))
        negative_weights = ((1.0 - cfg.TRAIN.RPN_POSITIVE_WEIGHT) /
                            np.sum(labels == 0))
    bbox_outside_weights[labels == 1, :] = positive_weights
    bbox_outside_weights[labels == 0, :] = negative_weights

    # map up to original set of anchors
    # labels,bbox_targets,bbox_inside_weights和bbox_outside_weights这些都是边框内部的anchors相关的信息，_unmap将其映射回包含所有边框的信息的变量中
    # total_anchors:所有的anchors(不论是否在框内外)的总数， inds_inside:所有在原图框内部的anchors的索引
    labels = _unmap(labels, total_anchors, inds_inside, fill=-1)    
    bbox_targets = _unmap(bbox_targets, total_anchors, inds_inside, fill=0)
    bbox_inside_weights = _unmap(bbox_inside_weights, total_anchors, inds_inside, fill=0)
    bbox_outside_weights = _unmap(bbox_outside_weights, total_anchors, inds_inside, fill=0)
    
    # labels
    labels = labels.reshape((1, height, width, A)).transpose(0, 3, 1, 2)        # height和weight是特征图尺寸,这里的A应该是9, 对应每个特征图点的anchors个数
    labels = labels.reshape((1, 1, A * height, width))
    rpn_labels = labels

    # bbox_targets
    rpn_bbox_targets = bbox_targets.reshape((1, height, width, A * 4)).transpose(0, 3, 1, 2)
    
    # bbox_inside_weights
    rpn_bbox_inside_weights = bbox_inside_weights.reshape((1, height, width, A * 4)).transpose(0, 3, 1, 2)

    # bbox_outside_weights
    rpn_bbox_outside_weights = bbox_outside_weights.reshape((1, height, width, A * 4)).transpose(0, 3, 1, 2)

    return rpn_labels,rpn_bbox_targets,rpn_bbox_inside_weights,rpn_bbox_outside_weights  
    

def _unmap(data, count, inds, fill=0):
    """
        Unmap a subset of item (data) back to the original set of items (of size count)
    """
    if len(data.shape) == 1:
        ret = np.empty((count, ), dtype=np.float32)
        ret.fill(fill)
        ret[inds] = data
    else:
        ret = np.empty((count, ) + data.shape[1:], dtype=np.float32)
        ret.fill(fill)
        ret[inds, :] = data
    return ret

def _compute_targets(ex_rois, gt_rois):
    """ 
        Compute bounding-box regression targets for an image.
    """

    assert ex_rois.shape[0] == gt_rois.shape[0]
    assert ex_rois.shape[1] == 4
    assert gt_rois.shape[1] == 5

    return bbox_transform(ex_rois, gt_rois[:, :4]).astype(np.float32, copy=False)

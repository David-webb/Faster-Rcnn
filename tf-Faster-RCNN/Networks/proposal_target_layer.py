# -*- coding: utf-8 -*-
"""
Created on Tue Jan  3 22:30:23 2017

@author: Kevin Liang (modifications)

Adapted from the official Faster R-CNN repo: 
https://github.com/rbgirshick/py-faster-rcnn/blob/master/lib/rpn/proposal_target_layer.py
"""

# --------------------------------------------------------
# Faster R-CNN
# Copyright (c) 2015 Microsoft
# Licensed under The MIT License [see LICENSE for details]
# Written by Ross Girshick and Sean Bell
# --------------------------------------------------------

import numpy as np
import numpy.random as npr
import tensorflow as tf

from Lib.bbox_overlaps import bbox_overlaps
from Lib.bbox_transform import bbox_transform
from Lib.faster_rcnn_config import cfg


def proposal_target_layer(rpn_rois, gt_boxes,_num_classes):
    '''
    Make Python version of _proposal_target_layer_py below Tensorflow compatible
    '''    
    rois,labels,bbox_targets,bbox_inside_weights,bbox_outside_weights = tf.py_func(_proposal_target_layer_py,[rpn_rois, gt_boxes,_num_classes],[tf.float32,tf.int32,tf.float32,tf.float32,tf.float32])

    rois = tf.reshape(rois,[-1,5] , name = 'rois') 
    labels = tf.convert_to_tensor(tf.cast(labels,tf.int32), name = 'labels')
    bbox_targets = tf.convert_to_tensor(bbox_targets, name = 'bbox_targets')
    bbox_inside_weights = tf.convert_to_tensor(bbox_inside_weights, name = 'bbox_inside_weights')
    bbox_outside_weights = tf.convert_to_tensor(bbox_outside_weights, name = 'bbox_outside_weights')
   
    return rois, labels, bbox_targets, bbox_inside_weights, bbox_outside_weights


def _proposal_target_layer_py(rpn_rois, gt_boxes,_num_classes):
    """
    Assign object detection proposals to ground-truth targets. Produces proposal
    classification labels and bounding-box regression targets.
    """
    
    # Proposal ROIs (0, x1, y1, x2, y2) coming from RPN
    # (i.e., rpn.proposal_layer.ProposalLayer), or any other source
    all_rois = rpn_rois

    # Include ground-truth boxes in the set of candidate rois
    # 将GT_boxes和rpn_rois拼接在一起，组成all_rois, 保证肯定有pos_rois
    zeros = np.zeros((gt_boxes.shape[0], 1), dtype=gt_boxes.dtype)
    all_rois = np.vstack(
        (all_rois, np.hstack((zeros, gt_boxes[:, :-1])))
    )

    # Sanity check: single batch only
    assert np.all(all_rois[:, 0] == 0), \
            'Only single item batches are supported'
            
    num_images = 1
    rois_per_image = cfg.TRAIN.BATCH_SIZE // num_images
    fg_rois_per_image = np.round(cfg.TRAIN.FG_FRACTION * rois_per_image).astype(np.int32)
    
    # Sample rois with classification labels and bounding box regression
    # targets
    # sample_rois，对all_rois进行了进一步的筛选
    # labels 保存了proposals的分类标签（目标类别）
    # rois 保存了 fg_rois 和 bg_rois， 顺序和labels一致
    # bbox_target (ndarray): N x 4K blob of regression targets, 其中N是rois的索引，K表示分类标签的总个数，4表示回归系数，axis=1的维度上，每个标签对应4个位置，初始为0，每个fg_roi的回归系数填在对应的cls位置
    # bbox_inside_weights (ndarray): N x 4K blob of loss weights. 分布同上
    labels, rois, bbox_targets, bbox_inside_weights = _sample_rois(
        all_rois, gt_boxes, fg_rois_per_image,
        rois_per_image, _num_classes)
    
   
    rois = rois.reshape(-1,5) # 5d = (cls, dx,dy,dw,dh)
    labels = labels.reshape(-1,1)
    bbox_targets = bbox_targets.reshape(-1,_num_classes*4)
    bbox_inside_weights = bbox_inside_weights.reshape(-1,_num_classes*4)

    bbox_outside_weights = np.array(bbox_inside_weights > 0).astype(np.float32)

    return np.float32(rois),labels,bbox_targets,bbox_inside_weights,bbox_outside_weights
    
def _get_bbox_regression_labels(bbox_target_data, num_classes):
    """
        Bounding-box regression targets (bbox_target_data) are stored in a
    compact form N x (class, tx, ty, tw, th)
    This function expands those targets into the 4-of-4*K representation used
    by the network (i.e. only one class has non-zero targets).
    Returns:
        bbox_target (ndarray): N x 4K blob of regression targets
        bbox_inside_weights (ndarray): N x 4K blob of loss weights
    """
    clss = bbox_target_data[:, 0]  # 所有roi_proposals的分类标签(bg_roi都为0)
    bbox_targets = np.zeros((clss.size, 4 * num_classes), dtype=np.float32) #  
    bbox_inside_weights = np.zeros(bbox_targets.shape, dtype=np.float32) #
    inds = np.where(clss > 0)[0]    # 前景图的索引
    for ind in inds:                  
        cls = clss[ind]             # 
        start = int(4 * cls)        #
        end = start + 4             # 
        bbox_targets[ind, start:end] = bbox_target_data[ind, 1:]
        bbox_inside_weights[ind, start:end] = (1, 1, 1, 1)
    return bbox_targets, bbox_inside_weights


def _compute_targets(ex_rois, gt_rois, labels):
    """
        Compute bounding-box regression targets for an image.
        返回值：
            二维数组，将每个roi_proposal的label和回归系数连接在一起
    """

    assert ex_rois.shape[0] == gt_rois.shape[0]
    assert ex_rois.shape[1] == 4
    assert gt_rois.shape[1] == 4

    targets = bbox_transform(ex_rois, gt_rois) # 回归系数矩阵，包含每个roi_proposal 对应回归系数
    if cfg.TRAIN.BBOX_NORMALIZE_TARGETS_PRECOMPUTED:        # 归一化？？？为什么要这样做？这里的均值是0，方差是1，也就是没有改变targets
        # Optionally normalize targets by a precomputed mean and stdev
        targets = ((targets - np.array(cfg.TRAIN.BBOX_NORMALIZE_MEANS))
                / np.array(cfg.TRAIN.BBOX_NORMALIZE_STDS))
    return np.hstack(
            (labels[:, np.newaxis], targets)).astype(np.float32, copy=False)

def _sample_rois(all_rois, gt_boxes, fg_rois_per_image, rois_per_image, num_classes):
    """Generate a random sample of RoIs comprising foreground and background
    examples.
    """
    # overlaps: (rois x gt_boxes)
    overlaps = bbox_overlaps(           # 计算Iou矩阵，其中行号是all_rois，列号是GT_boxes
        np.ascontiguousarray(all_rois[:, 1:5], dtype=np.float),
        np.ascontiguousarray(gt_boxes[:, :4], dtype=np.float))
    gt_assignment = overlaps.argmax(axis=1)     # all_rois中每个propersal_box对应的Iou最大的GT_box的索引  
    max_overlaps = overlaps.max(axis=1)         # all_rois中每个propersal_box对应的Iou最大的GT_box的Iou值
    labels = gt_boxes[gt_assignment, 4]         # 分类的类别标签 

    # Select foreground RoIs as those with >= FG_THRESH overlap
    fg_inds = np.where(max_overlaps >= cfg.TRAIN.FG_THRESH)[0]      # 最大Iou大于阈值的proposals的索引
    # Guard against the case when an image has fewer than fg_rois_per_image
    # foreground RoIs
    fg_rois_per_this_image = min(fg_rois_per_image, fg_inds.size)
    # Sample foreground regions without replacement
    if fg_inds.size > 0:
        fg_inds = npr.choice(fg_inds, size=fg_rois_per_this_image, replace=False)

    # Select background RoIs as those within [BG_THRESH_LO, BG_THRESH_HI)
    bg_inds = np.where((max_overlaps < cfg.TRAIN.BG_THRESH_HI) &
                       (max_overlaps >= cfg.TRAIN.BG_THRESH_LO))[0]
    # Compute number of background RoIs to take from this image (guarding
    # against there being fewer than desired)
    bg_rois_per_this_image = rois_per_image - fg_rois_per_this_image
    bg_rois_per_this_image = min(bg_rois_per_this_image, bg_inds.size)
    # Sample background regions without replacement
    if bg_inds.size > 0:
        bg_inds = npr.choice(bg_inds, size=bg_rois_per_this_image, replace=False)

    # The indices that we're selecting (both fg and bg)
    keep_inds = np.append(fg_inds, bg_inds)
    # Select sampled values from various arrays:
    labels = labels[keep_inds]  # 前景+背景roi的分类标签
    # Clamp labels for the background RoIs to 0
    # 背景roi的标签统一置为0, 实际上在配置文件中bg对应的类别__background__的索引就是0
    labels[fg_rois_per_this_image:] = 0 
    rois = all_rois[keep_inds]  # 前景+背景的所有rois

    # 求解rois中每个proposals的回归系数，将每个roi_proposal的label和回归系数连接在一起，得到二维数组bbox_target_data
    bbox_target_data = _compute_targets(
        rois[:, 1:5], gt_boxes[gt_assignment[keep_inds], :4], labels)

    # 这个操作比较难描述，看代码更直观
    # _get_bbox_regression_labels: expands those targets into the 4-of-4*K representation used
    # by the network (i.e. only one class has non-zero targets).
    #    bbox_target (ndarray): N x 4K blob of regression targets
    #    bbox_inside_weights (ndarray): N x 4K blob of loss weights
    bbox_targets, bbox_inside_weights = \
        _get_bbox_regression_labels(bbox_target_data, num_classes)

    return labels, rois, bbox_targets, bbox_inside_weights

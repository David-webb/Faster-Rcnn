# -*- coding: utf-8 -*-
"""
Created on Wed Jan 11 14:29:57 2017

@author: Kevin Liang

ROI pooling layer: Using tensorflow's crop_and_resize function as replacement.
crop_and_resize expects box indices in normalized coordinates.

Convolutional feature maps are cropped to a constant size of (14,14) and then
maxpooled to (7x7)
"""

import tensorflow as tf

def roi_pool(featureMaps,rois,im_dims):    
    '''
    Regions of Interest (ROIs) from the Region Proposal Network (RPN) are 
    formatted as:
    (image_id, x1, y1, x2, y2)
    
    Note: Since mini-batches are sampled from a single image, image_id = 0s

    注意：
        tf的实现方式还是和caffe原版的不太一样，主要体现在caffe原版实现的时候，
        是将特征图的逐通道上面的ROI区域划成了若干份，并从每一份中选取了最大值，
        也就是说，每一个通道的选值情况是不一样的！而tensorflow实现的ROI Pooling是先直接将ROI区域
        对应的特征割出来，并按照某一尺度(14×14)进行双线性插值resize，再使用tf.nn.max_pool将特征转化为更小的维度(7×7)
    '''
    with tf.variable_scope('roi_pool'):
        # Image that the ROI is taken from (minibatch of 1 means these will all be 0)
        box_ind = tf.cast(rois[:,0],dtype=tf.int32)
        
        # ROI box coordinates. Must be normalized and ordered to [y1, x1, y2, x2]
        # 这里对roi_proposals进行归一化(除以原图的weight/height)
        # 作用就是计算proposal在原图中的位置和比例，并基于此映射回特征图指定区域
        # 接着将每个proposal对应的特征图区域crop出来，再resize到固定尺寸（14*14），接着池化到7*7
        boxes = rois[:,1:]
        normalization = tf.cast(tf.stack([im_dims[:,1],im_dims[:,0],im_dims[:,1],im_dims[:,0]],axis=1),dtype=tf.float32)
        boxes = tf.div(boxes,normalization)
        boxes = tf.stack([boxes[:,1],boxes[:,0],boxes[:,3],boxes[:,2]],axis=1)  # y1, x1, y2, x2
        
        # ROI pool output size
        crop_size = tf.constant([14,14])
        
        # ROI pool
        pooledFeatures = tf.image.crop_and_resize(image=featureMaps, boxes=boxes, box_ind=box_ind, crop_size=crop_size)
        
        # Max pool to (7x7)
        pooledFeatures = tf.nn.max_pool(pooledFeatures, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')

    return pooledFeatures

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/12 11:33
# @Author  : 雷雨
# @File    : enums.py
# @Desc    :
import enum


class LiveInputType(enum.Enum):
    danmu = '弹幕'
    gift = '礼物'
    sc = 'sc'
    scheduler = '调度任务'
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import enum


class LiveInputType(enum.Enum):
    danmu = '弹幕'
    gift = '礼物'
    sc = 'sc'
    scheduler = '调度任务'
    user = 'user'
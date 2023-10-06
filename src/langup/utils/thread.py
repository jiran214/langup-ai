#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/15 15:47
# @Author  : 雷雨
# @File    : thread.py
# @Desc    :
import threading
from typing import List, Callable, Type

from bilibili_api import sync


def start_thread(job: Callable):
    """启动线程"""
    t = threading.Thread(target=job)
    t.start()
    return t


def Thread(
        listeners: List[Type['base.Listener']],
        uploader: 'base.Uploader'
):
    """初始化listeners和uploader，异步运行"""
    for listener_cls in listeners:
        listener = listener_cls([uploader.mq])
        start_thread(lambda: sync(listener.alisten()))
    t = start_thread(lambda: sync(uploader.wait()))
    return t


__all__ = [
    'sync',
    'start_thread',
    'Thread'
]
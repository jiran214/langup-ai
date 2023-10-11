#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
        uploader: 'base.Uploader',
        concurrent_num: int = 1
):
    """初始化listeners和uploader，异步运行"""
    threads = []
    for listener_cls in listeners:
        listener = listener_cls([uploader.mq])
        threads.append(start_thread(lambda: sync(listener.alisten())))

    for _ in range(concurrent_num):
        threads.append(
            start_thread(lambda: sync(uploader.wait()))
        )
    return threads


__all__ = [
    'sync',
    'start_thread',
    'Thread'
]
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import threading
from asyncio import iscoroutine, iscoroutinefunction
from typing import List, Callable, Type

from bilibili_api import sync


def start_thread(job: Callable):
    """启动线程"""
    if iscoroutinefunction(job):
        sync_job = lambda: sync(job())
    else:
        sync_job = job
    t = threading.Thread(target=sync_job)
    t.start()
    return t


__all__ = [
    'sync',
    'start_thread'
]
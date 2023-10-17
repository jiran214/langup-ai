#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/12 19:37
# @Author  : 雷雨
# @File    : user.py
# @Desc    :
import asyncio
import threading
import time
from threading import Lock

from pydantic import BaseModel

from langup import base


class ConsoleListener(base.Listener):
    SLEEP = 0
    console_event = threading.Event()

    class Schema(BaseModel):
        user_input: str

    def __init__(self, mq_list):
        super().__init__(mq_list)

    @staticmethod
    def clear_console():
        """保持控制台干净"""
        from langup import config
        if config.log['console'] and 'print' in config.log['console']:
            config.log['console'].remove('print')

    async def _alisten(self):
        self.console_event.wait()
        user_input = str(input('You: '))
        schema = self.Schema(user_input=user_input)
        self.console_event.clear()
        return schema

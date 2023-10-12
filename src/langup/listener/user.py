#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/12 19:37
# @Author  : 雷雨
# @File    : user.py
# @Desc    :
import asyncio
import time

from pydantic import BaseModel

from langup import base


class ConsoleListener(base.Listener):
    SLEEP = 1

    class Schema(BaseModel):
        user_input: str

    def __init__(self, mq_list):
        super().__init__(mq_list)
        print('123')

    @staticmethod
    def change_config():
        """保持控制台干净"""
        from langup import config
        if config.log['console']:
            config.log['console'].pop('print')
        config.debug = False

    async def _alisten(self):
        user_input = str(input('ConsoleListener输入:'))
        print('收到输入')
        schema = self.Schema(user_input=user_input)
        return schema

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/13 11:01
# @Author  : 雷雨
# @File    : simple.py
# @Desc    :
from langup import base, reaction, listener


class ConsoleReplyUP(base.Uploader):
    name = 'AI'
    system = '你是一位AI助手'
    temple = '{answer}。'

    def __init__(self):
        listeners = [listener.ConsoleListener]
        listener.ConsoleListener.console_event.set()
        super().__init__(listeners)

    def execute_sop(self, schema):
        print('thinking...')
        answer = self.brain.run(schema.user_input)
        print(f"{self.name}: {answer}")
        listener.ConsoleListener.console_event.set()
        return reaction.TTSSpeakReaction(audio_txt=answer)
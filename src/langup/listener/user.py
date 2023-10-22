#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/12 19:37
# @Author  : 雷雨
# @File    : user.py
# @Desc    :
import abc
import threading
from pydantic import BaseModel
from langup import base, config

from speech_recognition import UnknownValueError

from langup.reaction.voice import audio_lock
from langup.utils import utils
from langup.utils.converts import Audio2Text, Speech2Audio


class UserInputListener(base.Listener, abc.ABC):
    console_event = threading.Event()
    SLEEP = 0

    class Schema(BaseModel):
        user_input: str

    @abc.abstractmethod
    def get_input(self): ...

    async def _alisten(self):
        self.console_event.wait()
        user_input = self.get_input()
        schema = self.Schema(user_input=user_input)
        self.console_event.clear()
        return schema

    @staticmethod
    def clear_console():
        from langup import config
        """保持控制台干净"""
        if config.log['handlers'] and ('console' in config.log['handlers']):
            config.log['handlers'] = ['file']


class ConsoleListener(UserInputListener):

    def get_input(self):
        return str(input('You: '))


class SpeechListener(UserInputListener):
    def __init__(self, mq_list):
        self.convert = Speech2Audio()
        super().__init__(mq_list)

    def get_input(self):
        self.console_event.wait()
        while 1:
            utils.format_print('录音中...', end='')
            # 进行识别
            audio = self.convert.listen()
            utils.format_print('录音结束，识别中...', end='')
            try:
                res = Audio2Text.from_raw_data(raw_data=audio.get_wav_data(), data_fmt='wav')
                text = ' '.join(res)
                print('\nYou: ', end='')
                utils.format_print(f'{text}', color='green')
                self.console_event.clear()
                return text
            except UnknownValueError:
                utils.format_print('未识别到音频')

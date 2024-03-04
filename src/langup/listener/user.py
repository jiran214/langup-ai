#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/12 19:37
# @Author  : 雷雨
# @File    : user.py
# @Desc    :
import abc
import threading
from typing import Type, ClassVar

from pydantic import BaseModel, Field

import langup.core
from speech_recognition import UnknownValueError

import langup.listener.base
from langup.utils import utils
from langup.utils.converts import Audio2Text, Speech2Audio


class UserInputListener(langup.listener.base.Listener, abc.ABC):
    user_event: threading.Event = Field(default_factory=threading.Event)

    @abc.abstractmethod
    def get_input(self): ...

    async def alisten(self) -> str:
        self.user_event.wait()
        user_input = self.get_input()
        self.user_event.clear()
        return user_input


class ConsoleListener(UserInputListener):
    def get_input(self):
        return str(input('You: '))


class SpeechListener(UserInputListener):
    convert: Speech2Audio = Field(default_factory=Speech2Audio)

    def get_input(self):
        self.user_event.wait()
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
                self.user_event.clear()
                return text
            except UnknownValueError:
                utils.format_print('未识别到音频')

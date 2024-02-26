#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Literal, Optional

from bilibili_api import sync
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import chain, RunnablePassthrough
from pydantic import Field

from langup import listener, core, LLMChain, apis
from langup.utils import utils

_user_listener_map = {
    'console': listener.ConsoleListener,
    'speech': listener.SpeechListener
}


class UserInputReplyUP(core.Langup):
    name: str = 'AI'
    interval = 2
    system: str = '你是一位AI助手'
    listen: Literal['console', 'speech']

    @staticmethod
    @chain
    async def react(_dict):
        utils.format_print(f"{_dict['name']}: {_dict['output']}", color='green')
        await apis.voice.tts_speak(audio_txt=_dict['output'])
        _dict['listener'].user_event.set()

    def run(self):
        user_listener = _user_listener_map[self.listen]()
        runer = core.RunManager(
            interval=self.interval,
            extra_inputs={'name': self.name, 'listen': self.listen, 'listener': user_listener},
            chain=(
                LLMChain(self.system, self.human)
                | StrOutputParser()
                | self.react
            ),
        )
        user_listener.user_event.set()
        runer.single_run(user_listener)
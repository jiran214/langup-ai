#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from typing import Literal
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import chain, RunnablePassthrough, RunnableLambda

from langup import core, apis
from langup.listener.user import ConsoleListener, SpeechListener
from langup.utils import utils

_user_listener_map = {
    'console': ConsoleListener,
    'speech': SpeechListener
}


logger = logging.getLogger('langup.simple')


class UserInputReplyUP(core.Langup):
    name: str = 'AI'
    system: str = '你是一位AI助手'
    listen: Literal['console', 'speech']  # 输入方式

    @staticmethod
    @chain
    async def react(_dict):
        utils.format_print(f"{_dict['name']}: {_dict['output']}", color='green')
        await apis.voice.tts_speak(audio_txt=_dict['output'])

    def run(self):
        logger.debug('初始化 user_listener')
        user_listener = _user_listener_map[self.listen]()
        runer = core.RunManager(
            extra_inputs={'name': self.name, 'listen': self.listen},
            manager_config=self,
            chain=(
                RunnablePassthrough.assign(output=self._chain | StrOutputParser())
                | self.react | RunnableLambda(lambda _: user_listener.user_event.set())
            ),
        )
        runer.bind_listener(user_listener)
        user_listener.user_event.set()
        runer.run()
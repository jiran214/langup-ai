#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from typing import Literal, List, Callable, Union, Any, Iterable, Optional
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import chain, RunnablePassthrough, RunnableLambda
from pydantic import model_validator

from langup import core, apis
from langup.listener.base import Listener
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
                    RunnablePassthrough.assign(output=self._prompt | self.model | StrOutputParser())
                    | self.react | RunnableLambda(lambda _: user_listener.user_event.set())
            ),
        )
        runer.bind_listener(user_listener)
        user_listener.user_event.set()
        runer.forever_run()


class UP(core.Langup):
    react: Optional[Callable[[Union[str, dict]], Any]] = None
    listener: Optional[Listener] = None
    listeners: List[Listener] = []
    react_funcs: List[Callable[[Union[str, dict]], Any]] = []

    @model_validator(mode='after')
    def set_attrs(self):
        if self.react:
            self.react_funcs.append(self.react)
        if self.listener:
            self.listeners.append(self.listener)
        assert self.listeners and self.react_funcs, '未设置感知和行为'
        return self

    def run(self):
        runer = core.RunManager(
            manager_config=self,
            chain=(self._prompt | self.model | chain(self.react_func))
        )
        runer.forever_run()

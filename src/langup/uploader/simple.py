#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Literal, Optional

from pydantic import Field

from langup import base, reaction, listener
from langup.utils import utils

_user_listener_map = {
    'console': listener.ConsoleListener,
    'speech': listener.SpeechListener
}


class UserInputReplyUP(base.Uploader):
    """
    终端回复助手
    :param listen:  用户输入源
        - console 终端
        - speech 语音
    :param listeners:  感知
    :param concurrent_num:  并发数
    :param system:   人设

    :param openai_api_key:  openai秘钥
    :param openai_proxy:   http代理
    :param openai_api_base:  openai endpoint
    :param temperature:  gpt温度
    :param max_tokens:  gpt输出长度
    :param chat_model_kwargs:  langchain chatModel额外配置参数
    :param llm_chain_kwargs:  langchain chatChain额外配置参数

    :param brain:  含有run方法的类
    :param mq:  通信队列
    """
    up_sleep: int = Field(default=0)
    name: str = 'AI'
    system: str = Field(default='你是一位AI助手')
    temple: str = '{answer}。'
    listen: Literal['console', 'speech']

    def prepare(self):
        pass

    def init(self):
        listener.ConsoleListener.clear_console()
        super().init()

    def get_listeners(self):
        user_listener = _user_listener_map[self.listen]()
        user_listener.user_event.set()
        user_listener.clear_console()
        return [user_listener]

    def callback(self):
        if self.listeners[0] is listener.SpeechListener:
            listener.SpeechListener.user_event.set()
            self.logger.debug('callback set')

    def execute_sop(self, schema):
        utils.format_print('thinking...')
        answer = self.brain.run(schema.user_input)
        utils.format_print(f"{self.name}: {answer}", color='green')
        if self.listeners[0] is listener.ConsoleListener:
            listener.ConsoleListener.user_event.set()
        return reaction.TTSSpeakReaction(audio_txt=answer)
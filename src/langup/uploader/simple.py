#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Literal, Optional

from langup import base, reaction, listener
from langup.utils import utils


class UserInputReplyUP(base.Uploader):
    SLEEP = 0
    name = 'AI'
    system = '你是一位AI助手'
    temple = '{answer}。'

    __user_listener_map = {
        'console': listener.ConsoleListener,
        'speech': listener.SpeechListener
    }

    def __init__(
            self,
            listen: Literal['console', 'speech'],
            *args, **kwargs
    ):
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
        assert listen in self.__user_listener_map, "listen参数不存在"
        user_listener = self.__user_listener_map[listen]
        listeners = [user_listener]
        user_listener.console_event.set()
        user_listener.clear_console()
        super().__init__(listeners=listeners, *args, **kwargs)

    def callback(self):
        if self.listeners[0] is listener.SpeechListener:
            listener.SpeechListener.console_event.set()
            self.logger.debug('callback set')

    def execute_sop(self, schema):
        utils.format_print('thinking...')
        answer = self.brain.run(schema.user_input)
        utils.format_print(f"{self.name}: {answer}", color='green')
        if self.listeners[0] is listener.ConsoleListener:
            listener.ConsoleListener.console_event.set()
        return reaction.TTSSpeakReaction(audio_txt=answer)
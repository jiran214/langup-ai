#!/usr/bin/env python
# -*- coding: utf-8 -*-
from langup import base, reaction, listener


class ConsoleReplyUP(base.Uploader):
    name = 'AI'
    system = '你是一位AI助手'
    temple = '{answer}。'

    def __init__(self, *args, **kwargs):
        """
        终端回复助手
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
        listeners = [listener.ConsoleListener]
        listener.ConsoleListener.console_event.set()
        super().__init__(listeners=listeners, *args, **kwargs)

    def execute_sop(self, schema):
        print('thinking...')
        answer = self.brain.run(schema.user_input)
        print(f"{self.name}: {answer}")
        listener.ConsoleListener.console_event.set()
        return reaction.TTSSpeakReaction(audio_txt=answer)
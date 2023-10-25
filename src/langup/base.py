#!/usr/bin/env python
# -*- coding: utf-8 -*-
import abc
import asyncio
import queue

import time
from asyncio import iscoroutine
from logging import Logger
from typing import List, Optional, Callable, Union, Any

from bilibili_api import sync
from langchain.chat_models import ChatOpenAI
from pydantic import BaseModel, Field, ConfigDict

from langup import config, BrainType
from langup.brain.chains.llm import get_llm_chain
from langup.utils import mixins
from langup.utils.thread import start_thread
from langup.utils.utils import get_list


class MQ(abc.ABC):
    """Listener和Uploader通信"""

    @abc.abstractmethod
    def send(self, schema):
        ...

    @abc.abstractmethod
    def recv(self) -> Union[BaseModel, dict]:
        ...

    @abc.abstractmethod
    def empty(self):
        return


class SimpleMQ(queue.Queue, MQ):

    def recv(self) -> Union[BaseModel, dict]:
        return self.get()

    def send(self, schema):
        # 设置maxsize淘汰旧消息
        if self.maxsize != 0 and self.qsize() == self.maxsize:
            self.get()
        self.put(schema)


class Listener(BaseModel, abc.ABC):
    """监听api 通知绑定消息队列"""
    listener_sleep: int = 5
    Schema: Any = None
    mq_list: List[MQ] = []
    middlewares: Optional[List[Callable]] = []

    def init(self, mq: MQ, listener_sleep: Optional[int] = None):
        if listener_sleep is not None: self.listener_sleep = listener_sleep
        self.mq_list.append(mq)

    @abc.abstractmethod
    async def _alisten(self):
        return

    async def alisten(self):
        while 1:
            schema = await self._alisten()
            # 链式处理引用
            for mid in self.middlewares:
                mid(schema)
            if not schema:
                continue
            self.notify(schema)
            await asyncio.sleep(self.listener_sleep)

    def notify(self, schema):
        # pprint(schema)
        # 通知所有uploader
        for mq in self.mq_list:
            mq.send(schema)

    class Config:
        arbitrary_types_allowed = True


class Reaction(BaseModel, abc.ABC):
    """对llm结果做出回应"""
    block: bool = True

    @abc.abstractmethod
    async def areact(self):
        ...


class LLM(BaseModel):
    """
    :param system:  人设
    :param model_name:  gpt model
    :param openai_api_key:  openai秘钥
    :param openai_proxy:   http代理
    :param openai_api_base:  openai endpoint
    :param temperature:  gpt温度
    :param max_tokens:  gpt输出长度
    :param chat_model_kwargs:  langchain chatModel额外配置参数
    :param llm_chain_kwargs:  langchain chatChain额外配置参数
    """
    # 人设
    system: str = Field(default="You are a Bilibili UP")
    # llm配置
    model_name: str = Field(default="gpt-3.5-turbo", alias="model_name")
    openai_api_key: Optional[str] = None  # openai秘钥
    openai_proxy: Optional[str] = None  # http代理
    openai_api_base: Optional[str] = None  # openai endpoint
    temperature: Optional[float] = 0.7  # gpt温度
    max_tokens: Optional[int] = None  # gpt输出长度
    chat_model_kwargs: Optional[dict] = {}  # langchain chatModel额外配置参数
    llm_chain_kwargs: Optional[dict] = None  # langchain chatChain额外配置参数

    def get_brain(self):
        self.chat_model_kwargs.update(
            self.model_dump(include={
                'model_name', 'openai_api_key', 'openai_proxy', 'openai_api_base', 'temperature', 'max_tokens'
            })
        )
        self.chat_model_kwargs['openai_api_key'] = self.chat_model_kwargs['openai_api_key'] or config.openai_api_key
        chain = get_llm_chain(
            system=self.system,
            llm=ChatOpenAI(
                max_retries=2,
                request_timeout=60,
                **self.chat_model_kwargs or {},
            ),
            llm_chain_kwargs=self.llm_chain_kwargs
        )
        return chain

    class Config:
        protected_namespaces = ()


class Uploader(
    abc.ABC,
    LLM,
    mixins.ConfigImport,
    mixins.Logger,
    mixins.InitMixin,
    mixins.Looper
):
    """
    :param listeners: 感知
    :param concurrent_num: 并发数
    :param up_sleep: uploader 运行间隔时间
    :param listener_sleep: listener 运行间隔时间
    :param brain:  含有run方法的类
    :param mq:  通信队列
    """
    up_sleep: int = 1  # 运行间隔时间
    concurrent_num: int = 1   # 并发数
    listener_sleep: Optional[int] = None  # 运行间隔时间

    mq: MQ = Field(default_factory=SimpleMQ)
    logger: Optional[Logger] = None
    listeners: List[Listener] = []
    brain: Union[BrainType, None] = None

    def init(self):
        self.init_config()
        chain = self.get_brain()
        self.brain = chain
        self.listener_sleep = None
        self.listeners = self.get_listeners()
        self.prepare()

    @abc.abstractmethod
    def prepare(self): ...
    @abc.abstractmethod
    def get_listeners(self): ...
    @abc.abstractmethod
    def execute_sop(self, schema) -> Union[Reaction, List[Reaction]]: ...

    def callback(self):
        pass

    class Config:
        arbitrary_types_allowed = True
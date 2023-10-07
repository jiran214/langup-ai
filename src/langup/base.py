#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/15 14:50
# @Author  : 雷雨
# @File    : base.py
# @Desc    :
import abc
import json
import os
import queue
import time
import typing
from typing import List, Optional, Callable

from bilibili_api import sync
from langchain.chains.base import Chain
from pydantic import BaseModel

from langup.brain.chains.llm import get_simple_chat_chain
from langup.utils.thread import Thread, start_thread


class MQ(abc.ABC):
    """Listener和Uploader通信"""

    @abc.abstractmethod
    def send(self, schema):
        ...

    @abc.abstractmethod
    def recv(self) -> BaseModel:
        ...

    @abc.abstractmethod
    def empty(self):
        return


class SimpleMQ(queue.Queue, MQ):

    def recv(self) -> typing.Union[BaseModel, dict]:
        return self.get()

    def send(self, schema):
        if self.maxsize != 0 and self.qsize() == self.maxsize:
            self.get()
        self.put(schema)


class Listener(abc.ABC):
    """监听api 通知绑定消息队列"""
    sleep = 1

    def __init__(
            self,
            mq_list: List[MQ],
            middlewares: Optional[List[Callable]] = None
    ):
        self.mq_list = mq_list
        self.middlewares = middlewares or []

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

    def notify(self, schema):
        # pprint(schema)
        # 通知所有uploader
        for mq in self.mq_list:
            mq.send(schema)


class Record(BaseModel):
    """存档、日志"""
    listener_schema: typing.Any = None
    react_kwargs: Optional[dict] = None
    time_cost: Optional[str] = None
    created_time: Optional[str] = None

    def save_file(self, path):
        with open(path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(self.model_dump(), indent=4)+'\n')

    def print(self):
        print(self)

    def print(self):
        print(self)


class Reaction(BaseModel, abc.ABC):
    """对llm结果做出回应"""
    block: bool = True

    @abc.abstractmethod
    async def areact(self):
        ...


class Uploader(abc.ABC):
    default_system = "You are a Bilibili UP"
    system = None
    __is_init_config = False

    def __init__(
            self,
            listeners: List[typing.Type[Listener]],
            brain: Optional[Chain] = None,
            mq: MQ = SimpleMQ()
    ):
        self.mq = mq
        self.listeners = listeners
        self.brain = brain or get_simple_chat_chain(system=self.system or self.system or self.default_system)
        if self.__is_init_config is False:
            self.init_config()
            self.__is_init_config = True

    def init_config(self):
        """只执行一次"""
        from langup import config
        import openai
        for path in (config.tts['voice_path'], config.record['file_path'], config.convert['audio_path']):
            os.makedirs(path, exist_ok=True)

        if config.proxy:
            os.environ['HTTPS_PORXY'] = config.proxy
            os.environ['HTTP_PORXY'] = config.proxy
            openai.proxy = config.proxy

    @abc.abstractmethod
    def execute_sop(self, schema) -> typing.Union[Reaction, List[Reaction]]:
        ...

    async def wait(self):
        while 1:
            if self.mq.empty():
                time.sleep(1)
                continue
            schema = self.mq.recv()
            reaction_instance_list = self.execute_sop(schema)
            if not isinstance(
                    reaction_instance_list,
                    list
            ):
                reaction_instance_list = [reaction_instance_list]
            for reaction in reaction_instance_list:
                if reaction.block is True:
                    await reaction.areact()
                else:
                    start_thread(lambda: sync(reaction.areact()))

    def loop(self, block=True):
        t = Thread(
            listeners=self.listeners,
            uploader=self,
        )
        if block:
            t.join()
        return t
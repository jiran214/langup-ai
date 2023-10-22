#!/usr/bin/env python
# -*- coding: utf-8 -*-
import abc
import asyncio
import queue

import time
import typing
from asyncio import iscoroutine
from typing import List, Optional, Callable

from bilibili_api import sync
from pydantic import BaseModel

from langup import config, BrainType
from langup.brain.chains.llm import get_chat_chain
from langup.utils import mixins
from langup.utils.thread import Thread, start_thread


class MQ(abc.ABC):
    """Listener和Uploader通信"""

    @abc.abstractmethod
    def send(self, schema):
        ...

    @abc.abstractmethod
    def recv(self) -> typing.Union[BaseModel, dict]:
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
    SLEEP = 0
    Schema = None

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
            await asyncio.sleep(self.SLEEP)

    def notify(self, schema):
        # pprint(schema)
        # 通知所有uploader
        for mq in self.mq_list:
            mq.send(schema)


class Reaction(BaseModel, abc.ABC):
    """对llm结果做出回应"""
    block: bool = True

    @abc.abstractmethod
    async def areact(self):
        ...


class Uploader(
    abc.ABC,
    mixins.ConfigImport,
    mixins.Logger,
    mixins.InitMixin
):
    default_system = "You are a Bilibili UP"
    SLEEP = 1

    def __init__(
            self,
            listeners: List[typing.Type[Listener]],
            up_sleep: Optional[int] = None,
            listener_sleep: Optional[int] = None,
            concurrent_num=1,
            system: str = None,

            # llm配置
            openai_api_key: str = None,
            openai_proxy: str = None,
            openai_api_base: str = None,
            temperature: int = 0.7,
            max_tokens: int = None,
            chat_model_kwargs: Optional[dict] = None,
            llm_chain_kwargs: Optional[dict] = None,

            brain: typing.Union[BrainType, None] = None,
            mq: MQ = SimpleMQ(),
    ):
        """
        :param listeners: 感知
        :param concurrent_num: 并发数
        :param up_sleep: uploader 运行间隔时间
        :param listener_sleep: listener 运行间隔时间
        :param system:  人设

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
        self.SLEEP = up_sleep or 0
        self.listener_sleep = None
        self.system = None if system and system.lower() == 'default' else system
        self.listeners = listeners
        self.mq = mq
        self.concurrent_num = concurrent_num

        self.init_config(locals())

        self.brain = brain or get_chat_chain(
            system=self.system or self.system or self.default_system,
            openai_api_key=openai_api_key,
            openai_proxy=openai_proxy,
            openai_api_base=openai_api_base,
            temperature=temperature,
            max_tokens=max_tokens,
            chat_model_kwargs=chat_model_kwargs,
            llm_chain_kwargs=llm_chain_kwargs
        )

    @abc.abstractmethod
    def execute_sop(self, schema) -> typing.Union[Reaction, List[Reaction]]: ...

    async def wait(self):
        while 1:
            schema = self.mq.recv()
            t0 = time.time()
            if not isinstance(schema, list):
                schema_list = [schema]
            else:
                schema_list = schema
            for schema in schema_list:
                self.logger.debug('execute_sop')
                res = self.execute_sop(schema)
                if iscoroutine(res):
                    reaction_instance_list = await res
                else:
                    reaction_instance_list = res
                # execute_sop 返回空代表过滤
                if not reaction_instance_list:
                    continue
                if not isinstance(reaction_instance_list, list):
                    reaction_instance_list = [reaction_instance_list]
                react_kwargs = {}
                task_list = []
                for reaction in reaction_instance_list:
                    react_kwargs.update(reaction.model_dump())
                    if reaction.block is True:
                        task_list.append(asyncio.create_task(reaction.areact()))
                    else:
                        start_thread(lambda: sync(reaction.areact()))
                self.logger.debug('run task_list')
                await asyncio.gather(*task_list)
                if config.log['handlers']:
                    self.record(
                        listener_kwargs=schema.model_dump() if isinstance(schema, BaseModel) else schema,
                        time_cost=str(time.time() - t0).split('.')[0],
                        react_kwargs=react_kwargs
                    )
                self.logger.debug('callback')
                self.callback()
                await asyncio.sleep(self.SLEEP)

    def loop(self, block=True):
        for listener in self.listeners:
            if self.listener_sleep: listener.SLEEP = self.listener_sleep
        threads = Thread(
            listeners=self.listeners,
            uploader=self,
            concurrent_num=self.concurrent_num
        )
        if block:
            [t.join() for t in threads]
        return threads

    def callback(self):
        pass

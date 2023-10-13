#!/usr/bin/env python
# -*- coding: utf-8 -*-
import abc
import asyncio
import json
import os
import queue
import time
import typing
from datetime import datetime
from pprint import pprint
from typing import List, Optional, Callable

from bilibili_api import sync
from pydantic import BaseModel

from langup import config, BrainType
from langup.brain.chains.llm import get_simple_chat_chain
from langup.utils.logger import get_logging_logger
from langup.utils.thread import Thread, start_thread

_is_init_config = False


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

    def notify(self, schema):
        # pprint(schema)
        # 通知所有uploader
        for mq in self.mq_list:
            mq.send(schema)


class Record(BaseModel):
    """存档、日志"""
    listener_schema: Optional[typing.Any] = None
    react_kwargs: Optional[dict] = None
    time_cost: Optional[str] = None
    created_time: Optional[str] = None

    def save_file(self, path):
        with open(path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(self.model_dump(), indent=4)+'\n')

    def print(self):
        pprint(self.model_dump(exclude_none=True, exclude_defaults=True))


class Reaction(BaseModel, abc.ABC):
    """对llm结果做出回应"""
    block: bool = True

    @abc.abstractmethod
    async def areact(self):
        ...


class Uploader(abc.ABC):
    default_system = "You are a Bilibili UP"
    system = None
    SLEEP = 1

    def __init__(
            self,
            listeners: List[typing.Type[Listener]],
            brain: typing.Union[BrainType, None] = None,
            concurrent_num=1,
            mq: MQ = SimpleMQ()
    ):
        self.listeners = listeners
        self.mq = mq
        self.concurrent_num = concurrent_num
        global _is_init_config
        if _is_init_config is False:
            self.init_config()
            _is_init_config = True
        self.brain = brain or get_simple_chat_chain(system=self.system or self.system or self.default_system)
        self.logger = get_logging_logger(file_name=self.__class__.__name__)

    def init_config(self):
        """只执行一次"""
        from langup import config
        import openai
        for listener in self.listeners:
            if change_config := getattr(listener, 'change_config', None):
                change_config()
                print(f'<listener: {listener.__name__}修改配置>')
        for path in (config.tts['voice_path'], config.log['file_path'], config.convert['audio_path']):
            path = config.work_dir + path
            os.makedirs(path, exist_ok=True)
        config.tts['voice_path'] = config.work_dir + config.tts['voice_path']
        config.log['file_path'] = config.work_dir + config.log['file_path']
        config.convert['audio_path'] = config.work_dir + config.convert['audio_path']

        if config.proxy:
            os.environ['HTTPS_PORXY'] = config.proxy
            os.environ['HTTP_PORXY'] = config.proxy
            openai.proxy = config.proxy

    @abc.abstractmethod
    def execute_sop(self, schema) -> typing.Union[Reaction, List[Reaction]]:
        ...

    def record(self, listener_schema, time_cost, react_kwargs):
        rcd = Record(
            listener_schema=listener_schema,
            time_cost=time_cost,
            created_time=str(datetime.now()),
            react_kwargs=react_kwargs
        )
        if 'print' in config.log['console']:
            rcd.print()
        if 'file' in config.log['console']:
            rcd.save_file(path=f"{config.log['file_path']}{self.__class__.__name__}Record.txt")

    async def wait(self):
        while 1:
            if self.mq.empty():
                time.sleep(self.SLEEP)
                continue
            schema = self.mq.recv()
            t0 = time.time()
            reaction_instance_list = self.execute_sop(schema)
            # execute_sop 返回空代表过滤
            if not reaction_instance_list:
                continue
            if not isinstance(reaction_instance_list, list):
                reaction_instance_list = [reaction_instance_list]
            react_kwargs = {}
            task_list = []
            for reaction in reaction_instance_list:
                if config.log['console']:
                    react_kwargs.update(reaction.model_dump())
                if reaction.block is True:
                    task_list.append(asyncio.create_task(reaction.areact()))
                else:
                    start_thread(lambda: sync(reaction.areact()))
            if config.log['console']:
                self.record(listener_schema=schema, time_cost=str(time.time()-t0).split('.')[0], react_kwargs=react_kwargs)
            await asyncio.gather(*task_list)

    def loop(self, block=True):
        threads = Thread(
            listeners=self.listeners,
            uploader=self,
            concurrent_num=self.concurrent_num
        )
        if block:
            [t.join() for t in threads]
        return threads
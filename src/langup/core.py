#!/usr/bin/env python
# -*- coding: utf-8 -*-
import abc
import asyncio
import logging
import os
import threading
from typing import Union, Any, Iterable, Optional, Dict, List

import bilibili_api
import dotenv
import openai
from bilibili_api import sync
from pydantic import BaseModel, Field, model_validator
from langchain_core.runnables import Runnable, chain, RunnableAssign

from langup import config, SchedulingEvent
from langup.listener import SchedulerWrapper
from langup.listener.base import Listener
from langup.utils.consts import WELCOME
from langup.utils.utils import Continue, get_list, format_print

logger = logging.getLogger('langup')


class RunManager(BaseModel, abc.ABC):
    chain: Union[Runnable]
    extra_inputs: dict = {}
    manager_config: 'Langup'
    listeners: List[Listener] = []

    def model_post_init(self, __context: Any) -> None:
        if self.manager_config.retriever_map:
            self.chain = (RunnableAssign(**self.manager_config.retriever_map) | self.chain)
        # 调度监听
        if self.schedulers:
            sche_listener = SchedulerWrapper()
            for e in self.schedulers:
                sche_listener.scheduler.add_job(**e.get_scheduler_inputs())
            sche_listener.run()
            self.bind_listener(sche_listener)
            return

    async def aconnect(self, listener: Listener):
        # 初始化
        if config.first_init is False:
            dotenv.load_dotenv()
            if 'sessdata' in os.environ:
                config.set_bilibili_config(os.environ.get('sessdata'), os.environ.get('buvid3'))
            if config.welcome_tip:
                format_print(WELCOME, color='green')
            if config.test_net:
                requestor, url = openai.Model._ListableAPIResource__prepare_list_requestor()
                response, _, api_key = requestor.request("get", url, None, None, request_timeout=10)
            if config.proxy:
                os.environ['HTTPS_PORXY'] = config.proxy
                os.environ['HTTP_PORXY'] = config.proxy
                bilibili_api.settings.proxy = config.proxy
        config.first_init = True

        while 1:
            res = await listener.alisten()
            # 收到list类型，逐一处理
            data_list = get_list(res)
            for data_dict in data_list:
                logger.debug(f'listen:{data_dict}')
                if not data_dict:
                    logger.debug(f'no data_dict')
                    continue
                try:
                    await self.chain.ainvoke({**data_dict, **self.extra_inputs})
                except Continue as e:
                    logger.info(f'忽略执行:{e}')
                    continue
            logger.debug(f'sleep:{self.interval}')
            await asyncio.sleep(self.manager_config.interval)

    def bind_listener(self, l: Listener):
        self.listeners.append(l)

    def run(self):
        assert self.listeners, '未设置 listeners'
        if len(self.listeners) == 1:
            sync(self.aconnect(self.listeners.pop()))
            return

        threads = []

        for l in self.listeners:
            t = threading.Thread(target=self.single_run, args=(l,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        return threads

    class Config:
        arbitrary_types_allowed = True


class Langup(BaseModel):
    system: str
    human: str = '{text}'

    retriever_map: Optional[Dict[str, Runnable]] = Field(None, description='langchain检索器map')
    schedulers: Iterable[SchedulingEvent] = Field([], description='调度事件列表')
    interval: int = 2

    @model_validator(mode='after')
    def check_prompt(self):
        for prompt_var in self.retriever_map:
            assert prompt_var in self.human, f'请在Langup.human中传入{prompt_var}模版变量'

    @staticmethod
    @chain
    @abc.abstractmethod
    async def react(_dict):
        pass

    @abc.abstractmethod
    def run(self):
        pass

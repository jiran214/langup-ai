#!/usr/bin/env python
# -*- coding: utf-8 -*-
import abc
import asyncio
import logging
import os
import threading
from typing import Union, Any, Iterable, Optional, Dict, List, Tuple
from urllib.request import getproxies

import bilibili_api
import dotenv
import openai
from bilibili_api import sync
from pydantic import BaseModel, Field, model_validator
from langchain_core.runnables import Runnable, chain, RunnableAssign

from langup import config
from langup.listener.utils import SchedulerWrapper
from langup.listener.schema import SchedulingEvent
from langup.listener.base import Listener
from langup.utils.consts import WELCOME
from langup.utils.utils import Continue, get_list, format_print

logger = logging.getLogger('langup')


class Langup(BaseModel):
    system: str
    human: str = '{text}'

    retriever_map: Optional[Dict[str, Runnable]] = Field({}, description='langchain检索器map')
    schedulers: Iterable[SchedulingEvent] = Field([], description='调度事件列表')
    interval: int = 0

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

    class Config:
        arbitrary_types_allowed = True


class RunManager(BaseModel):
    chain: Runnable
    manager_config: Any  # 类型Langup有bug
    extra_inputs: dict = {}
    listener_items: List[Tuple[Listener, int]] = []

    def model_post_init(self, __context: Any) -> None:
        # 初始化
        if config.first_init is False:
            logger.debug('初始化RunManager')
            dotenv.load_dotenv()
            if 'sessdata' in os.environ:
                config.set_bilibili_config(os.environ.get('sessdata'), os.environ.get('buvid3'))
            if config.welcome_tip:
                format_print(WELCOME, color='green')
            if config.test_net:
                requestor, url = openai.Model._ListableAPIResource__prepare_list_requestor()
                response, _, api_key = requestor.request("get", url, None, None, request_timeout=10)
            if config.proxy:
                os.environ['HTTPS_PROXY'] = config.proxy
                os.environ['HTTP_PROXY'] = config.proxy
                bilibili_api.settings.proxy = config.proxy
            else:
                # 系统代理手动设置
                global_proxies = getproxies()
                os.environ['HTTPS_PROXY'] = global_proxies.get('https') and global_proxies['https'].replace('https', 'http')
                os.environ['HTTP_PROXY'] = global_proxies.get('http')

            logger.debug(f"代理环境 https:{os.environ.get('HTTPS_PROXY')} http:{os.environ.get('HTTP_PROXY')}")
        config.first_init = True
        if self.manager_config.retriever_map:
            self.chain = (RunnableAssign(**self.manager_config.retriever_map) | self.chain)
        # 调度监听
        if self.manager_config.schedulers:
            logger.debug('初始化sche_listener')
            sche_listener = SchedulerWrapper()
            for e in self.manager_config.schedulers:
                sche_listener.scheduler.add_job(**e.get_scheduler_inputs())
            logger.debug('启动sche_listener')
            sche_listener.run()
            self.bind_listener(sche_listener)
            return

    async def aconnect(self, listener: Listener):
        while 1:
            res = await listener.alisten()
            # 收到list类型，逐一处理
            data_list = get_list(res)
            for res in data_list:
                logger.debug(f'收到消息{listener.__class__.__name__}:{res}')
                if not res:
                    continue
                try:
                    if isinstance(res, str):
                        data_dict = {'text': res}
                    else:
                        data_dict = res
                    inputs = {**data_dict, **self.extra_inputs}
                    logger.debug(f'运行中chain {inputs=}')
                    await self.chain.ainvoke(inputs)
                except Continue as e:
                    logger.info(f'已过滤:{e}')
                    continue
            logger.debug(f'暂停:{self.manager_config.interval}')
            await asyncio.sleep(self.manager_config.interval)

    def bind_listener(self, l: Listener, thread_num=1):
        self.listener_items.append((l, thread_num))

    def run(self):
        """一个listener对应一个线程运行，对应多个aconnect协程"""
        logger.debug('开始运行RunManager')
        assert self.listener_items, '未设置 listeners'
        threads = []

        async def coroutine_task(tasks):
            await asyncio.gather(*tasks)

        for l, n in self.listener_items:
            if n == 1:
                sync(self.aconnect(l))
                continue
            coroutines = [asyncio.create_task(self.aconnect(l)) for _ in range(n)]
            t = threading.Thread(target=sync, args=(coroutine_task(coroutines),))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        return threads

    class Config:
        arbitrary_types_allowed = True

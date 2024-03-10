#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import logging
import os
import threading
from typing import Any, Iterable, Optional, Dict, List, Tuple, Union, Callable, Generator, AsyncGenerator
from urllib.request import getproxies

import bilibili_api
import dotenv
import openai
from bilibili_api import sync
from langchain_core.runnables import Runnable

from langup import config
from langup.listener.utils import SchedulerWrapper
from langup.listener.schema import SchedulingEvent
from langup.listener.base import AsyncListener
from langup.utils.consts import WELCOME
from langup.utils.utils import Continue, format_print, ReactType

logger = logging.getLogger('langup')


def first_init():
    if config.first_init is False:
        dotenv.load_dotenv(verbose=True)
        if not config.credential and 'sessdata' in os.environ:
            config.set_bilibili_cookies(
                **{k: os.environ.get(k) for k in ('sessdata', 'buvid3', 'bili_jct', 'dedeuserid', 'ac_time_value')})
            logger.debug(f'初始化bilibili_config from env: {config.auth.credential.get_cookies()}')
        if config.welcome_tip:
            format_print(WELCOME, color='green')
        if config.test_net:
            logger.debug('测试外网环境...')
            requestor, url = openai.Model._ListableAPIResource__prepare_list_requestor()
            response, _, api_key = requestor.request("get", url, None, None, request_timeout=10)
        if proxy := (config.proxy or getproxies().get('http')):
            logger.debug(f'已设置全代理:{proxy}')
            os.environ['HTTPS_PROXY'] = proxy
            os.environ['HTTP_PROXY'] = proxy
            bilibili_api.settings.proxy = proxy
        logger.debug(f"代理环境 https:{os.environ.get('HTTPS_PROXY')} http:{os.environ.get('HTTP_PROXY')}")
    config.first_init = True


class Process:
    def __init__(self):
        self.threads = []
        first_init()

    async def handle(self, chain, msg, interval, extra_inputs):
        logger.debug(f'收到消息:{msg}')
        if not msg:
            return
        try:
            inputs = {**msg, **extra_inputs}
            logger.debug(f'运行中chain')
            await chain.ainvoke(inputs)
        except Continue as e:
            logger.info(f'已过滤:{e}')
            return
        if interval:
            logger.debug(f'等待中:{interval}')
            await asyncio.sleep(interval)

    def add_thread(
            self,
            generator: Union[Generator, AsyncGenerator, AsyncListener],
            handler: Runnable,
            extra_inputs: dict = None,
            interval: int = 0
    ):
        async def sync_gen_task():
            for msg in generator:
                await self.handle(handler, msg, interval, extra_inputs)

        async def async_gen_task():
            async for msg in generator:
                await self.handle(handler, msg, interval, extra_inputs)

        async def listener_task():
            while 1:
                msg = await generator.alisten()
                await self.handle(handler, msg, interval, extra_inputs)

        if isinstance(generator, Generator):
            task = sync_gen_task
        elif isinstance(generator, AsyncGenerator):
            task = sync(async_gen_task())
        elif isinstance(generator, AsyncListener):
            task = sync(listener_task())
        else:
            raise ValueError(f'不支持的类型:{type(generator)}')
        self.threads.append(threading.Thread(target=task))

    def add_sche_thread(self, events: Iterable[SchedulingEvent], handler: Runnable):
        logger.debug('初始化plugin schedulers')
        sche_listener = SchedulerWrapper()
        for e in events:
            sche_listener.scheduler.add_job(**e.get_scheduler_inputs())
        logger.debug('启动sche_listener')
        sche_listener.run()
        self.add_thread(sche_listener, handler)

    def run(self):
        for t in self.threads:
            t.start()
        for t in self.threads:
            t.join()

    def loop(self):
        self.run()

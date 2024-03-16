#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import functools
import logging
import os
import threading
from typing import Any, Iterable, Optional, Dict, List, Tuple, Union, Callable, Generator, AsyncGenerator, Type
from urllib.request import getproxies

import bilibili_api
import dotenv
import openai
from bilibili_api import sync
from langchain_core.runnables import Runnable

from langup import config, ListenerType
from langup.builder.base import Flow
from langup.listener.base import AsyncListener
from langup.utils.consts import WELCOME
from langup.utils.utils import Continue, format_print

logger = logging.getLogger('langup')


def first_init():
    if config.first_init is False:
        dotenv.load_dotenv(verbose=True)
        if not config.credential and 'sessdata' in os.environ:
            config.set_bilibili_cookies(
                **{k: os.environ.get(k) for k in ('sessdata', 'buvid3', 'bili_jct', 'dedeuserid', 'ac_time_value')})
            logger.debug(f'初始化bilibili_config from env: {config.credential.get_cookies()}')
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

    def add_thread(
            self,
            generator: ListenerType,
            handler: Union[Runnable, Flow],
            extra_inputs: Optional[dict] = None,
            interval: int = 0
    ):
        if isinstance(handler, Flow):
            handler = handler.get_flow()

        async def handle(msg):
            logger.debug(f'收到消息:{msg}')
            if not msg:
                return
            try:
                inputs = {**msg, **extra_inputs}
                logger.debug(f'运行中chain')
                await handler.ainvoke(inputs)
            except Continue as e:
                logger.info(f'已过滤:{e}')
                return
            if interval:
                logger.debug(f'等待中:{interval}')
                await asyncio.sleep(interval)

        async def sync_gen_task():
            for msg in generator:
                await handle(msg)

        async def async_gen_task():
            async for msg in generator:
                await handle(msg)

        async def listener_task():
            while 1:
                msg = await generator.alisten()
                await handle(msg)

        if isinstance(generator, Generator):
            task = sync_gen_task
        elif isinstance(generator, AsyncGenerator):
            task = sync(async_gen_task())
        elif isinstance(generator, AsyncListener):
            task = sync(listener_task())
        else:
            raise ValueError(f'不支持的类型:{type(generator)}')
        self.threads.append(threading.Thread(target=task))

    def run(self):
        for t in self.threads:
            t.start()
        for t in self.threads:
            t.join()

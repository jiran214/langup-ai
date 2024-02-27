#!/usr/bin/env python
# -*- coding: utf-8 -*-
import abc
import asyncio
import logging
import os
import threading
from typing import Union, Any, Iterable

import bilibili_api
import dotenv
import openai
from bilibili_api import sync
from pydantic import BaseModel
from langchain_core.runnables import Runnable, chain

from langup import config
from langup.utils.consts import WELCOME
from langup.utils.utils import Continue, get_list, format_print

logger = logging.getLogger('langup')


class Listener(BaseModel, abc.ABC):
    """监听api 通知绑定消息队列"""

    def model_post_init(self, __context: Any) -> None:
        self.check_config()

    def check_config(self):
        pass

    @abc.abstractmethod
    async def alisten(self):
        return

    class Config:
        arbitrary_types_allowed = True


class RunManager(BaseModel, abc.ABC):
    interval: int = 10
    chain: Union[Runnable]
    extra_inputs: dict = {}

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
            await asyncio.sleep(self.interval)

    def single_run(self, listener: Listener):
        sync(self.aconnect(listener))

    def multiple_run(self, listeners: Iterable[Listener]):
        threads = []

        for l in listeners:
            t = threading.Thread(target=self.single_run, args=(l,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        return threads

    class Config:
        arbitrary_types_allowed = True


# 高层api 接口
class Langup(BaseModel):
    system: str
    human: str = '{text}'
    interval: int = 2

    @staticmethod
    @chain
    @abc.abstractmethod
    async def react(_dict):
        pass

    @abc.abstractmethod
    def run(self):
        pass



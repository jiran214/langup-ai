import asyncio
import functools
import json
import os
import threading
import time
from asyncio import iscoroutine
from datetime import datetime

import bilibili_api
import openai
from bilibili_api import Credential
from dotenv import load_dotenv
from pydantic import BaseModel

from langup import config
from langup.utils import consts
from langup.utils.logger import get_logging_logger
from langup.utils.utils import Record, format_print, get_list, start_thread

_is_init_config = False


class ConfigImport(BaseModel):

    @classmethod
    def from_json_file(cls, json_path):
        json_data = json.loads(fp=json_path, encoding='utf-8')
        up = cls(**json_data)
        return up


class InitMixin:
    """初始化、检查"""
    __init_lock = threading.Lock()

    def check(self):
        assert config.openai_api_key, '请提供api_key'
        # 检查网络环境
        if config.test_net:
            # self.format_print('\r检查网络环境中...')
            assert self.test_net(), '当前网络环境不能访问openai，请检查！'

    def test_net(self):
        requestor, url = openai.Model._ListableAPIResource__prepare_list_requestor()
        response, _, api_key = requestor.request(
            "get", url, None, None, request_timeout=10
        )
        return response

    def init_config(self):
        with self.__init_lock:
            global _is_init_config
            if _is_init_config is False:
                self.__init_config()
                _is_init_config = True

    def __init_config(self: 'base.Uploader'):
        """只执行一次"""
        from langup import config
        self.logger = get_logging_logger(file_name=self.__class__.__name__)
        # 环境变量读取
        is_load = load_dotenv(verbose=True)
        print(f'读取.env文件变量:{str(is_load)}')
        credential = Credential(
            sessdata=os.environ.get('sessdata'),
            bili_jct=os.environ.get('bili_jct'),
            buvid3=os.environ.get('buvid3'),
            dedeuserid=os.environ.get('dedeuserid'),
            ac_time_value=os.environ.get('ac_time_value'),
        )
        if credential.sessdata and credential.buvid3:
            config.credential = credential

        import openai  # 环境变量加载好后再导入
        # 路径配置
        for path in (config.tts['voice_path'], config.log['file_path'], config.convert['audio_path']):
            path = config.work_dir + path
            os.makedirs(path, exist_ok=True)
        config.tts['voice_path'] = config.work_dir + config.tts['voice_path']
        config.log['file_path'] = config.work_dir + config.log['file_path']
        config.convert['audio_path'] = config.work_dir + config.convert['audio_path']
        # 代理配置
        if config.proxy:
            os.environ['HTTPS_PORXY'] = config.proxy
            os.environ['HTTP_PORXY'] = config.proxy
            bilibili_api.settings.proxy = config.proxy
        if proxy := (config.proxy or self.openai_proxy):
            openai.proxy = proxy
        # key 配置
        config.openai_api_key = config.openai_api_key or self.openai_api_key or openai.api_key or os.environ.get('OPENAI_API_KEY')
        openai.api_key = config.openai_api_key
        self.check()
        if config.welcome_tip:
            format_print(consts.WELCOME, color='green')


class Logger:

    @functools.cached_property
    def record_path(self):
        return f"{config.log['file_path']}{self.__class__.__name__}Record.jsonl"

    def record(self, listener_kwargs, time_cost, react_kwargs):
        rcd = Record(
            listener_kwargs=listener_kwargs,
            time_cost=time_cost,
            created_time=str(datetime.now()),
            react_kwargs=react_kwargs
        )
        path = self.record_path
        with open(path, 'a', encoding='utf-8') as file:
            line = json.dumps(rcd.model_dump(), ensure_ascii=False) + '\n'
            file.write(line)
        # with open(path, 'a', encoding='utf-8') as f:
        #     f.write(json.dumps(rcd.model_dump(), indent=4) + '\n')
        self.logger.info(f"完成一轮回应:{rcd.model_dump()}")

    def query(self):
        if not os.path.exists(self.record_path):
            return []
        with open(self.record_path, 'r', encoding='utf-8') as f:
            try:
                data_list = [json.loads(line) for line in f]
                return data_list
            except Exception as e:
                raise Exception(f'Record文件:{self.record_path}序列化失败,请确认是否手动修修改过\n{e}')


class Looper:

    async def wait(self: 'base.Uploader'):
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
                reactions = await res if iscoroutine(res) else res
                # execute_sop 返回空代表过滤
                if reactions is None:
                    continue
                await self.handle_reaction(t0, schema, reactions)

    async def handle_reaction(self: 'base.Uploader', t0, schema, reactions):
        reaction_instance_list = get_list(reactions)
        react_kwargs = {}
        task_list = []
        for reaction in reaction_instance_list:
            react_kwargs.update(reaction.model_dump())
            if reaction.block is True:
                task_list.append(asyncio.create_task(reaction.areact()))
            else:
                start_thread(reaction.areact)
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
        await asyncio.sleep(self.up_sleep)

    def loop(self: 'base.Uploader', block=True):
        self.init()
        threads = []
        for listener in self.listeners:
            listener.init(mq=self.mq, listener_sleep=self.listener_sleep)
            threads.append(start_thread(listener.alisten))

        for _ in range(self.concurrent_num):
            threads.append(start_thread(self.wait))
        if block:
            [t.join() for t in threads]
        return threads
import json
import os
import threading
from datetime import datetime

import bilibili_api
import openai

from langup import config
from langup.utils.utils import Record


_is_init_config = False


class ConfigImport:

    @classmethod
    def from_json_file(cls, json_path):
        json_data = json.load(fp=json_path, encoding='utf-8')
        up = cls(**json_data)
        return up


class InitMixin:
    """初始化、检查"""
    logger: None
    __init_lock = threading.Lock()

    def check(self):
        assert config.openai_api_key or os.environ.get('OPENAI_API_KEY'), '请提供api_key'
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

    def format_print(self, text):
        print(f"\033[1;32m{text}\033[0m")

    def init_config(self,init_kwargs):
        with self.__init_lock:
            global _is_init_config
            if _is_init_config is False:
                self.__init_config(init_kwargs)
                _is_init_config = True

    def __init_config(self, init_kwargs):
        """只执行一次"""
        from langup import config
        import openai
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
        if proxy := (config.proxy or init_kwargs.get('openai_proxy')):
            openai.proxy = proxy
        # key 配置
        config.openai_api_key = config.openai_api_key or init_kwargs.get('openai_api_key') or openai.api_key
        openai.api_key = config.openai_api_key
        self.check()
        if config.welcome_tip:
            self.format_print("""==========================================================
    ██       █████  ███    ██  ██████  ██    ██ ██████  
    ██      ██   ██ ████   ██ ██       ██    ██ ██   ██ 
    ██      ███████ ██ ██  ██ ██   ███ ██    ██ ██████  
    ██      ██   ██ ██  ██ ██ ██    ██ ██    ██ ██      
    ███████ ██   ██ ██   ████  ██████   ██████  ██      
==========================================================""")


class Logger:
    logger: None

    @property
    def record_path(self):
        return f"{config.log['file_path']}{self.__class__.__name__}Record.txt"

    def record(self, listener_kwargs, time_cost, react_kwargs):
        rcd = Record(
            listener_kwargs=listener_kwargs,
            time_cost=time_cost,
            created_time=str(datetime.now()),
            react_kwargs=react_kwargs
        )
        path = self.record_path
        with open(path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(rcd.model_dump(), indent=4) + '\n')
        self.logger.info(f"完成一轮回应:{rcd.model_dump()}")

    def query(self):
        with open(self.record_path, 'a+', encoding='utf-8') as f:
            try:
                return json.loads('[' + ''.join(line for line in f.readlines()).replace('}\n{', '},{') + ']')
            except Exception as e:
                raise Exception(f'Record文件:{self.record_path}序列化失败,请确认是否手动修应该过\n{e}')
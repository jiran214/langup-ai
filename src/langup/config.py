"""
全局配置，基本可以作为Uploader参数传入
"""
import functools
from typing import Union
import asyncio
import os
from typing import Optional, Literal
from urllib.request import getproxies

import httpx
from bilibili_api import Credential


work_dir = './'

# 声音配置
tts = {
    "voice": "zh-CN-XiaoyiNeural",
    "rate": "+0%",
    "volume": "+0%",
    "voice_path": work_dir + 'voice/'
}

# 语音识别
convert = {
    "audio_path": work_dir + "audio/",
    # SpeechRecognition Module
    "speech_rec": {
        # 常用的
        'phrase_threshold': 1.2,  # 在我们将说话音频视为短语之前的最小说话秒数 - 低于此值的将被忽略（用于过滤点击声和爆音）
        'energy_threshold': 1300,  # 最小音频能量以进行录制

        'adjust_for_ambient_noise': False,  # 噪声调节energy_threshold
        'dynamic_energy_threshold': False,  # 动态调节energy_threshold
        'dynamic_energy_adjustment_damping': 0.15,
        'dynamic_energy_ratio': 1.5,
        'pause_threshold': 0.8,  # 在一个短语被认为完成之前的无语音音频秒数
        'operation_timeout': None,  # 内部操作（例如 API 请求）开始后超时的秒数，或 ``None`` 表示没有超时限制
        'non_speaking_duration': 0.5  # 录制两侧的无语音音频秒数
    }
}

# 字幕控件
subtitle = {'text_color': "#fa9a19", 'font': ("SimHei", 35, 'bold')}

root = os.path.dirname(__file__)


class AuthManager:
    credential: Optional[Credential] = None
    openai_kwargs: dict = {}

    def set_bilibili_config(self,
            sessdata: str, buvid3: str, bili_jct: Optional[str] = None, dedeuserid: Optional[str] = None, ac_time_value: Optional[str] = None
        ):
        self.credential = Credential(sessdata=sessdata, buvid3=buvid3, bili_jct=bili_jct, dedeuserid=dedeuserid, ac_time_value=ac_time_value)

    def set_openai_config(
        self,
        openai_api_key=None,
        openai_proxy=None,
        openai_api_base=None,
        model="gpt-3.5-turbo",
        **openai_kwargs
    ):
        os.environ.setdefault('OPENAI_API_KEY', openai_api_key)
        openai_kwargs.update(
            openai_proxy=openai_proxy,
            openai_api_key=openai_api_key,
            openai_api_base=openai_api_base,
            model=model
        )
        for key in openai_kwargs.keys():
            if V := openai_kwargs.get(key):
                self.openai_kwargs[key] = V

    @functools.cache
    def check_bilibili_config(self):
        self.credential.raise_for_no_sessdata()
        self.credential.raise_for_no_buvid3()
        asyncio.run(self.credential.check_valid())

    @functools.cache
    def check_openai_config(self):
        assert os.environ.get('OPENAI_API_KEY')


auth = AuthManager()
set_bilibili_config = auth.set_bilibili_config
set_openai_config = auth.set_openai_config

# 全局proxy，区别于openai_proxy
proxy = None
test_net = False
welcome_tip = False

first_init = False

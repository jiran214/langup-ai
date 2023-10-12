import os
from typing import Union

from bilibili_api import Credential


credential: Union['Credential', None] = None
work_dir = './'

tts = {
    "voice": "zh-CN-XiaoyiNeural",
    "rate": "+0%",
    "volume": "+0%",
    "voice_path": 'voice/'
}

log = {
    "console": ["print"],  # print打印生成信息, file文件存储生成信息
    "file_path": "logs/"
}

convert = {
    "audio_path": "audio/"
}

root = os.path.dirname(__file__)
openai_api_key = None  # sk-...
openai_baseurl = None  # https://{your_domain}/v1
proxy = None  # 代理
debug = True

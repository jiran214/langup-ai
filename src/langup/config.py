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
    "console": ["print"],  # print,file
    "file_path": "logs/"
}

convert = {
    "audio_path": "audio/"
}

root = os.path.dirname(__file__)
openai_api_key = None
openai_baseurl = None
proxy = None
debug = False

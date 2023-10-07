import os
from typing import Union

from bilibili_api import Credential

credential: Union['Credential', None] = None

tts = {
    "voice": "zh-CN-XiaoyiNeural",
    "rate": "+0%",
    "volume": "+0%",
    "voice_path": './voice/'
}

record = {
    "console": ["print", 'file'],  # print,file
    "file_path": "./"
}

convert = {
    "audio_path": "./audio/"
}

openai_api_key = None
proxy = None
debug = False
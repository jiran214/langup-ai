"""
全局配置，基本可以作为Uploader参数传入
"""
import os
from typing import Union

from bilibili_api import Credential


VERSION = '0.0.9'
credential: Union['Credential', None] = None
work_dir = './'

tts = {
    "voice": "zh-CN-XiaoyiNeural",
    "rate": "+0%",
    "volume": "+0%",
    "voice_path": 'voice/'
}

log = {
    "handlers": ["console"],  # console打印日志到控制台, file文件存储
    "file_path": "logs/"
}
convert = {
    "audio_path": "audio/",
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


root = os.path.dirname(__file__)
openai_api_key = None  # sk-...
openai_api_base = None  # https://{your_domain}/v1
proxy = None  # 代理
debug = False

test_net = True
welcome_tip = True

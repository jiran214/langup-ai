import asyncio
import threading
import time
import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = ""

import edge_tts
from pprint import pprint
from pygame import mixer, time as pygame_time
from langup import config


audio_lock = threading.Lock()


async def tts_save(text):
    tts_cfg = {**config.tts, 'proxy': config.proxy}
    voice_path = tts_cfg.pop('voice_path')
    tts = edge_tts.Communicate(text=text, **tts_cfg)
    path = f"{voice_path}{str(time.time())[:10]}.mp3"
    await tts.save(path)
    return path


def play_sound(file_path: str):
    with audio_lock:
        # 播放生成的语音文件
        mixer.init()
        mixer.music.load(file_path)
        mixer.music.play()
        while mixer.music.get_busy():
            pygame_time.Clock().tick(10)

        mixer.music.stop()
        mixer.quit()


def list_voices():
    pprint(asyncio.run(edge_tts.list_voices()))


async def tts_speak(audio_txt: str):
    path = await tts_save(audio_txt)
    play_sound(path)



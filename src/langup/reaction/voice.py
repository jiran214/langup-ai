import asyncio
import threading
import time
import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = ""

from pprint import pprint
import edge_tts
from pygame import mixer, time as pygame_time

from langup import config, base


audio_lock = threading.Lock()


tts_cfg = config.tts.copy()
tts_cfg['proxy'] = config.proxy
voice_path = tts_cfg.pop('voice_path')


async def tts_save(text):
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


class TTSSpeakReaction(base.Reaction):
    audio_txt: str

    async def areact(self):
        path = await tts_save(self.audio_txt)
        play_sound(path)



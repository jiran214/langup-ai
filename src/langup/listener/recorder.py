import copy
import threading
import time
from collections import deque

import speech_recognition as sr
import pyaudio
import wave
from array import array

from speech_recognition import UnknownValueError



FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
CHUNK = 1024
# RECORD_SECONDS = 10
FILE_NAME = "RECORDING_{}.wav"
# 设置阈值
high_threshold = 1000  # 高阈值
start_seconds_threshold = 2   # 连续高音几秒后开始录制
low_threshold = 500   # 低阈值
stop_seconds_threshold = 2  # 连续静音几秒后结束一次录制
percent = 0.8


audio = pyaudio.PyAudio()  # instantiate the pyaudio


class Recorder:

    def __init__(self):
        self.index = 0
        self.lock = threading.Lock()
        self.is_record = False

    def recording(self):
        # starting recording
        frames = []
        high_vol_window = [0 for _ in range(int(RATE / CHUNK * start_seconds_threshold))]
        high_percent_num = percent * len(high_vol_window)
        low_vol_window = [0 for _ in range(int(RATE / CHUNK * stop_seconds_threshold))]
        low_percent_num = percent * len(low_vol_window)
        # recording prerequisites
        stream = audio.open(format=FORMAT, channels=CHANNELS,
                            rate=RATE,
                            input=True,
                            frames_per_buffer=CHUNK)
        while 1:
            while 1:
                data = stream.read(CHUNK)
                data_chunk = array('h', data)
                vol = max(data_chunk)
                # 使用变量的值构建输出字符串
                # 打印输出字符串
                state = (vol >= high_threshold)
                output = f"当前音量: {vol} state:{state}"
                print(f'{output}', end="   ")
                if state:
                    frames.append(data)
                    print("something said")
                else:
                    # time.sleep(1)
                    print("nothing")
                if self.is_record is False:
                    # 是否满足开始录制条件
                    high_vol_window.append(state)
                    if sum(high_vol_window) >= high_percent_num:
                        high_vol_window.clear()
                        self.is_record = True
                        continue
                else:
                    # 是否满足结束录制条件
                    low_vol_window.append(not state)
                    if sum(low_vol_window) >= low_percent_num:
                        low_vol_window.clear()
                        self.is_record = False
                        break

            print('prepare save...')
            threading.Thread(target=self.record_save, args=(copy.deepcopy(frames),)).start()
            frames = []
            # end of recording
            # stream.stop_stream()
            # stream.close()

    def record_save(self, frames):
        # writing to file
        audio.terminate()
        file_name = FILE_NAME.format(self.index)
        self.index += 1
        wavfile = wave.open(file_name, 'wb')
        wavfile.setnchannels(CHANNELS)
        wavfile.setsampwidth(audio.get_sample_size(FORMAT))
        wavfile.setframerate(RATE)
        wavfile.writeframes(b''.join(frames))  # append frames recorded to file
        wavfile.close()
        print(f'存储成功:{file_name}')


class RecognizeWorker:

    def __init__(self):
        self.r = sr.Recognizer()
        self.r.energy_threshold = 900
        self.r.dynamic_energy_threshold = False
        # self.r.dynamic_energy_ratio = 2
        self.mic = sr.Microphone()

    def run(self):
        print('录音中...', end='')
        with self.mic as source:
            # self.r.adjust_for_ambient_noise(source)
            audio = self.r.listen(source)
        # 进行识别
        print('录音结束，识别中...', end='')
        try:
            test = self.r.recognize_google(audio, language='cmn-Hans-CN')  # 这样设置language可以支持中文
            # 最后将识别的文字打印出来
            print(test)
        except UnknownValueError:
            print('未识别到音频')

    def loop(self):
        while 1:
            self.run()
            time.sleep(0.5)


if __name__ == '__main__':
    RecognizeWorker().loop()
"""
该模块来源于：https://github.com/SocialSisterYi/bcut-asr
做了python3.8的适配
"""

# import logging
import time
from os import PathLike
from pathlib import Path
from typing import Literal, Optional, List, Union
import urllib3
import requests
from .orm import (ResourceCompleteRspSchema, ResourceCreateRspSchema,
                  ResultRspSchema, ResultStateEnum, TaskCreateRspSchema)


urllib3.disable_warnings()

__version__ = '0.0.2'

API_REQ_UPLOAD    = 'https://member.bilibili.com/x/bcut/rubick-interface/resource/create' # 申请上传
API_COMMIT_UPLOAD = 'https://member.bilibili.com/x/bcut/rubick-interface/resource/create/complete' # 提交上传
API_CREATE_TASK   = 'https://member.bilibili.com/x/bcut/rubick-interface/task' # 创建任务
API_QUERY_RESULT  = 'https://member.bilibili.com/x/bcut/rubick-interface/task/result' # 查询结果

SUPPORT_SOUND_FORMAT = Literal['flac', 'aac', 'm4a', 'mp3', 'wav']


class APIError(Exception):
    '接口调用错误'
    def __init__(self, code, msg) -> None:
        self.code = code
        self.msg = msg
        super().__init__()
    def __str__(self) -> str:
        return f'{self.code}:{self.msg}'


class BcutASR:
    '必剪 语音识别接口'
    session: requests.Session
    sound_name: str
    sound_bin: bytes
    sound_fmt: SUPPORT_SOUND_FORMAT
    __in_boss_key: str
    __resource_id: str
    __upload_id: str
    __upload_urls: List[str]
    __per_size: int
    __clips: int
    __etags: List[str]
    __download_url: str
    task_id: str
    
    def __init__(self, file: Optional[Union[str, PathLike]] = None) -> None:
        self.session = requests.Session()
        # 取消验证证书
        self.session.verify = False
        self.session.trust_env = False
        self.task_id = None
        self.__etags = []
        if file:
            self.set_data(file)
    
    def set_data(self,
                 file: Optional[Union[str, PathLike]] = None,
                 raw_data: Optional[bytes] = None,
                 data_fmt: Optional[SUPPORT_SOUND_FORMAT] = None
                 ) -> None:
        '设置欲识别的数据'
        if file:
            if not isinstance(file, (str, PathLike)):
                raise TypeError('unknow file ptr')
            # 文件类
            file = Path(file)
            self.sound_bin = open(file, 'rb').read()
            suffix = data_fmt or file.suffix[1:]
            self.sound_name = file.name
        elif raw_data:
            # bytes类
            self.sound_bin = raw_data
            suffix = data_fmt
            self.sound_name = f'{int(time.time())}.{suffix}'
        else:
            raise ValueError('none set data')
        if suffix not in ['flac', 'aac', 'm4a', 'mp3', 'wav']:
            raise TypeError('format is not support')
        self.sound_fmt = suffix
        # logging.info(f'加载文件成功: {self.sound_name}')
    
    def upload(self) -> None:
        '申请上传'
        if not self.sound_bin or not self.sound_fmt:
            raise ValueError('none set data')
        resp = self.session.post(API_REQ_UPLOAD, data={
            'type': 2,
            'name': self.sound_name,
            'size': len(self.sound_bin),
            'resource_file_type': self.sound_fmt,
            'model_id': 7
        })
        resp.raise_for_status()
        resp = resp.json()
        code = resp['code']
        if code:
            raise APIError(code, resp['message'])
        resp_data = ResourceCreateRspSchema.parse_obj(resp['data'])
        self.__in_boss_key = resp_data.in_boss_key
        self.__resource_id = resp_data.resource_id
        self.__upload_id = resp_data.upload_id
        self.__upload_urls = resp_data.upload_urls
        self.__per_size = resp_data.per_size
        self.__clips = len(resp_data.upload_urls)
        # logging.info(f'申请上传成功, 总计大小{resp_data.size // 1024}KB, {self.__clips}分片, 分片大小{resp_data.per_size // 1024}KB: {self.__in_boss_key}')
        self.__upload_part()
        self.__commit_upload()
        
    def __upload_part(self) -> None:
        '上传音频数据'
        for clip in range(self.__clips):
            start_range = clip * self.__per_size
            end_range = (clip + 1) * self.__per_size
            # logging.info(f'开始上传分片{clip}: {start_range}-{end_range}')
            resp = self.session.put(self.__upload_urls[clip],
                data=self.sound_bin[start_range:end_range],
            )
            resp.raise_for_status()
            etag = resp.headers.get('Etag')
            self.__etags.append(etag)
            # logging.info(f'分片{clip}上传成功: {etag}')
    
    def __commit_upload(self) -> None:
        '提交上传数据'
        resp = self.session.post(API_COMMIT_UPLOAD, data={
            'in_boss_key': self.__in_boss_key,
            'resource_id': self.__resource_id,
            'etags': ','.join(self.__etags),
            'upload_id': self.__upload_id,
            'model_id': 7
        })
        resp.raise_for_status()
        resp = resp.json()
        code = resp['code']
        if code:
            raise APIError(code, resp['message'])
        resp_data = ResourceCompleteRspSchema.parse_obj(resp['data'])
        self.__download_url = resp_data.download_url
        # logging.info(f'提交成功')
    
    def create_task(self) -> str:
        '开始创建转换任务'
        resp = self.session.post(API_CREATE_TASK, json={
            'resource': self.__download_url,
            'model_id': '7'
        })
        resp.raise_for_status()
        resp = resp.json()
        code = resp['code']
        if code:
            raise APIError(code, resp['message'])
        resp_data = TaskCreateRspSchema.parse_obj(resp['data'])
        self.task_id = resp_data.task_id
        # logging.info(f'任务已创建: {self.task_id}')
        return self.task_id
    
    def result(self, task_id: Optional[str] = None) -> ResultRspSchema:
        '查询转换结果'
        resp = self.session.get(API_QUERY_RESULT, params={
            'model_id': 7,
            'task_id': task_id or self.task_id
        })
        resp.raise_for_status()
        resp = resp.json()
        code = resp['code']
        if code:
            raise APIError(code, resp['message'])
        return ResultRspSchema.parse_obj(resp['data'])


def get_audio_text_by_bcut(file_path):
    asr = BcutASR(file_path)
    asr.upload()  # 上传文件
    asr.create_task()  # 创建任务

    # 轮询检查结果
    while True:
        result = asr.result()
        # 判断识别成功
        if result.state == ResultStateEnum.COMPLETE:
            break

    # 解析字幕内容
    subtitle = result.parse()
    # 判断是否存在字幕
    if subtitle.has_data():
        # 输出srt格式
        return [s.transcript for s in subtitle.utterances]
    return None
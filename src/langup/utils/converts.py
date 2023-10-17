#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os.path
import random
from typing import Optional, Literal
from typing import Union

import tiktoken

from langup import config
from langup.api.bcut_asr import get_audio_text_by_bcut
from langup.api.bilibili.video import Video
from langup.utils import consts


class Audio2Text:
    @classmethod
    async def from_bilibili_video(
            cls,
            v: Video
    ):
        res = await v.get_subtitle_datalist()
        if res:
            return [item['content'] for item in res]
        else:
            # 部分视频没有字幕，先下载视频，使用api转文字
            path = f"{config.convert['audio_path']}{v.get_aid() or v.get_bvid()}"
            new_path = await v.download_audio(path)
            return cls.from_file_path(new_path)

    @classmethod
    def from_file_path(cls, path):
        return get_audio_text_by_bcut(path)


class SummaryGenerator:
    encoding = tiktoken.get_encoding('cl100k_base')

    def __init__(
            self,
            limit_token: Union[int, str, None] = None,
            limit_length: Optional[int] = None,
            compress_mode: Literal['random', 'left'] = 'random'
    ):
        assert limit_token or limit_length, '请提供限制条件'
        if limit_token and isinstance(limit_token, str):
            limit_token = consts.model_token[limit_token]
        self.limit_token = limit_token and limit_token * 0.9
        self.limit_length = limit_length
        self.compress_mode = compress_mode

    def generate(self, content_list, join_char='\n') -> str:
        content = join_char.join(content_list)
        if self.limit_length and len(content) > self.limit_length:
            # 按长度压缩
            length = 0

            # random mode
            if self.compress_mode == 'random':
                index_list = list(range(len(content_list)))
                insert_index_list = []
                random.shuffle(index_list)
                for index in index_list:
                    c = content_list[index]
                    length += len(c)
                    if length > self.limit_length:
                        break
                    insert_index_list.append(index)
                insert_index_list.sort()
                content = join_char.join([content_list[index] for index in insert_index_list])

            # left mode
            elif self.compress_mode == 'left':
                content = ''
                for c in content_list:
                    length += len(c)
                    if length > self.limit_length:
                        break
                    content += join_char + c

        elif self.limit_token and len(self.encoding.encode(content)) > self.limit_token:
            # 按token压缩
            token = 0

            # random mode
            if self.compress_mode == 'random':
                index_list = list(range(len(content_list)))
                insert_index_list = []
                random.shuffle(index_list)
                for index in index_list:
                    c = content_list[index]
                    token += len(self.encoding.encode(c))
                    if token > self.limit_token:
                        break
                    insert_index_list.append(index)
                insert_index_list.sort()
                content = join_char.join([content_list[index] for index in insert_index_list])

            # left mode
            elif self.compress_mode == 'left':
                content = ''
                for c in content_list:
                    token += len(self.encoding.encode(c))
                    if token > self.limit_token:
                        break
                    content += join_char + c

        return content


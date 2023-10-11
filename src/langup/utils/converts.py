#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Union

from langup import config
from langup.api.bcut_asr import get_audio_text_by_bcut
from langup.api.bilibili.video import Video


class Audio2Txt:
    @classmethod
    async def from_bilibili_video(
            cls,
            bvid: Union[None, str] = None,
            aid: Union[None, int] = None
    ):
        v = Video(bvid=bvid, aid=aid, credential=config.credential)
        res = await v.get_subtitle_datalist()
        if res:
            return [item['content'] for item in res]
        else:
            # 部分视频没有字幕，先下载视频，使用api转文字
            path = f"{config.convert['audio_path']}{aid or bvid}"
            new_path = await v.download_audio(path)
            return cls.from_file_path(new_path)

    @classmethod
    def from_file_path(cls, path):
        return get_audio_text_by_bcut(path)


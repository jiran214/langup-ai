#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Optional, List

import httpx
from bilibili_api import video, HEADERS
from requests import Session

from langup.api.bilibili.schema import BiliNoteView

session = Session()
session.trust_env = False


class Video(video.Video):
    __bn_info = None

    async def download_audio(self, file_path):
        # 获取视频下载链接
        download_url_data = await self.get_download_url(0)
        # 解析视频下载信息
        detecter = video.VideoDownloadURLDataDetecter(data=download_url_data)
        streams = detecter.detect_best_streams()
        # 有 MP4 流 / FLV 流两种可能
        if detecter.check_flv_stream() == True:
            file_path += 'flv.mp3'
        else:
            file_path += 'm4s.mp3'
        # MP4 流下载
        await self.download_url(streams[1].url, file_path, "音频流")
        return file_path

    @staticmethod
    async def download_url(url: str, out: str, info: str):
        # 下载函数
        async with httpx.AsyncClient(headers=HEADERS) as sess:
            resp = await sess.get(url)
            length = resp.headers.get('content-length')
            with open(out, 'wb') as f:
                process = 0
                for chunk in resp.iter_bytes(1024):
                    if not chunk:
                        break
                    process += len(chunk)
                    # print(f'下载 {info} {process} / {length}')
                    f.write(chunk)

    @property
    def info(self) -> BiliNoteView:
        assert self.__info
        if not self.__bn_info:
            self.__bn_info = BiliNoteView(**self.__info)
        return self.__bn_info

    async def get_subtitle_datalist(self) -> Optional[List[dict]]:
        if not self.__info:
            await self.get_info()
        subtitles = self.info.subtitle.get('list')
        if not subtitles:
            # 没有字幕
            return
        if not subtitles[0]['subtitle_url']:
            cid = self.info.cid
            subtitle = await self.get_subtitle(cid)
            subtitles = subtitle['subtitles']
            if not (subtitles and subtitles[0]['subtitle_url']):
                # 没有AI字幕
                return
            # AI字幕
            url = 'https:' + subtitles[0]['subtitle_url']
            r = session.get(url)
            # [{'from': 0.0, 'to': 7.0, 'location': 2, 'content': ''},
            return r.json()['body']
        # 普通字幕(好像没了)
        return subtitles[0]['subtitle_url']

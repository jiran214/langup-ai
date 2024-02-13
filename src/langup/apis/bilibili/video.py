#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import os
from typing import Optional, List

import httpx
from bilibili_api import video, HEADERS, sync
from requests import Session
from langup.apis.bilibili.schema import BiliNoteView, NoteAISummary

session = Session()
session.headers = {
    'User-Agent': """Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0""",
    'referer': """https://www.bilibili.com/video/BV1wj411y7pq/?spm_id_from=333.1007.tianma.1-2-2.click&vd_source=3d9525035e29a1361801ce820151e270""",
    'origin': "https://www.bilibili.com",
}
session.trust_env = False


def trans_time(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime("%H:%M")


class Video(video.Video):
    __bn_info: BiliNoteView = None
    __summary_info: NoteAISummary = None

    async def download_audio(self, file_path):
        if os.path.exists(file_path + 'm4s.mp3'):
            return file_path + 'm4s.mp3'
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

    async def get_ai_summary(self, page_index=0):
        """获取AI总结"""
        json_data = await self.get_ai_conclusion(page_index=page_index)
        self.__summary_info = NoteAISummary(**json_data['model_result'])
        return self.__summary_info

    async def get_md_summary(self):
        """格式化总结内容成md"""
        if not self.__summary_info:
            await self.get_ai_summary()
        md = (
            "## {title}\n"
            "author: {author}\n"
            "summary: {summary}\n"
            "{outlines}"
        )

        outline = (
            "- {time}: {content}"
        )
        outlines = ""
        for outline_item in self.__summary_info.outline:
            outlines += f"\n### {outline_item.title}\n" + '\n'.join([
                outline.format(time=trans_time(part_item.timestamp), content=part_item.content)
                for part_item in outline_item.part_outline
            ])
        md = md.format(
            title=self.info.title,
            author=self.info.owner['name'],
            summary=self.__summary_info.summary,
            outlines=outlines
        )
        return md


if __name__ == '__main__':
    v = Video(bvid='BV1wj411y7pq')
    print(sync(v.get_md_summary()))

#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import time
from typing import Optional, List, Iterable

from bilibili_api.comment import send_comment, CommentResourceType
from langchain_core.runnables import RunnablePassthrough, chain

from langup import config, set_logger, Process, runables, apis
from langup.listener.bilibili import SessionAtGenerator
from langup.utils import converts
from langup.utils.utils import Continue

config.set_bilibili_cookies(sessdata='xxx', buvid3='xxx', bili_jct='xxx')
logger = set_logger()

summary_generator = converts.SummaryGenerator(
    limit_token=2048,
    compress_mode='random'
)


@chain
# 新版本官方提供了总结接口
async def get_summary(_dict):
    # 获取summary
    video = apis.bilibili.video.Video(aid=_dict['aid'], credential=config.credential)
    summary = await video.get_md_summary()
    logger.debug("Video API 该视频无AI总结，尝试提取字幕")
    if not summary:
        video_content_list = await converts.Audio2Text.from_bilibili_video(video)
        if video.info.duration > 60 * 60:
            logger.debug(f'过滤,视频时长超出限制: {60 * 60}')
            raise Continue('提取摘要失败')
        if not video_content_list:
            logger.error('查找字幕资源失败')
            raise Continue('提取摘要失败')
        summary = summary_generator.generate(video_content_list)
        record = summary.replace('\n', '')
        logger.debug(f"获取摘要成功:{record[:10]}...{record[-10:]}")
    return summary


def run(
        system: str = "你是一位B站用戶，帮助我总结视频！",
        human: str = (
                '视频内容如下\n'
                '###\n'
                '{summary}\n'
                '###'
        ),
        interval: int = 120,
        signals: Iterable[str] = ('总结一下',),  # 部分暗号会被屏蔽
        reply_temple: str = (
                '{output}'
                '本条回复由AI生成，'
                '由@{nickname}召唤。'
        ),
        openai_api_key=None,
        openai_kwargs: dict = {}
):
    process = Process()

    @chain
    async def react(_dict):
        content = reply_temple.format(output=_dict['output'], nickname=_dict['user_nickname'])
        logger.info(f'准备发送文本:{content}')
        await send_comment(text=content, type_=CommentResourceType.VIDEO, oid=_dict['aid'],
                           credential=config.credential)

    _chain = (
            RunnablePassthrough.assign(summary=get_summary)
            | RunnablePassthrough.assign(
                output=runables.Prompt(system=system, human=human) | runables.LLM(openai_api_key, **openai_kwargs))
            | react
    )
    process.add_thread(SessionAtGenerator(signals=signals), _chain, interval=interval)
    process.run()


if __name__ == '__main__':
    run(signals=['锐评一下', '来看看', '评论一下'])

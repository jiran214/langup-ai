#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from operator import itemgetter
from typing import Literal, Any, Iterable, Optional

from bilibili_api.comment import send_comment, CommentResourceType
from bilibili_api.dynamic import send_dynamic, BuildDynamic
from bilibili_api.session import send_msg, EventType
from langchain_core.runnables import chain
from pydantic import Field

from langup import Process, ReflectFlow, config
from langup.apis import voice
from langup.apis.bilibili.video import get_summary
from langup.listener.bilibili import ChatListener, SessionAtGenerator, LiveListener
from langup.listener.schema import SchedulingEvent, KeywordReply, LiveInputType
from langup.listener.user import ConsoleListener, SpeechListener
from langup.listener.utils import SchedulerWrapper
from langup.utils import utils

logger = logging.getLogger('langup')


class HumanInReplyUP(ReflectFlow):
    async def _areact(self, _content):
        # 语音实时识别回复
        # 语音识别参数见config.convert
        utils.format_print(f"AI: {_content}", color='green')
        await voice.tts_speak(audio_txt=_content)

    def run(self, listen: Literal['console', 'speech']):
        process = Process()
        _user_listener_map = {
            'console': ConsoleListener,
            'speech': SpeechListener
        }
        process.add_thread(_user_listener_map[listen](), self.get_flow())
        process.run()


class DynamicUP(ReflectFlow):
    """
    DynamicUP(...)
        events=[
            SchedulingEvent(input='请感谢大家的关注！', time='10m'),
            SchedulingEvent(input='请感谢大家的关注！', time='0:36')
        ]
    )
    """

    async def _areact(self, _content):
        await send_dynamic(BuildDynamic.create_by_args(text=_content), credential=config.credential)

    def run(self, events: Iterable[SchedulingEvent]):
        process = Process()
        process.add_thread(SchedulerWrapper(events=events), self.get_flow())
        process.run()


class ChatUP(ReflectFlow):
    async def _areact(self, _dict):
        await send_msg(config.credential, _dict['sender_uid'], EventType.TEXT, _dict[self.llm_output_key])

    def run(self):
        process = Process()
        process.add_thread(ChatListener(), self.get_flow())
        process.run()


class VideoCommentUP(ReflectFlow):
    context: dict = {'summary': itemgetter('aid') | chain(get_summary)}
    system: str = Field("你是一位B站用戶，帮助我总结视频！", description='system role提示词')
    human: str = Field(
        '视频内容如下\n'
        '###\n'
        '{summary}\n'
        '###',
        description='user role提示词'
    )
    reply_temple: str = Field(
        '{output}'
        '本条回复由AI生成，'
        '由@{nickname}召唤。',
        description='回复评论模版'
    )

    async def _areact(self, _dict):
        content = self.reply_temple.format(output=_dict[self.llm_output_key], nickname=_dict['user_nickname'])
        logger.info(f'准备发送文本:{content}')
        await send_comment(text=content, type_=CommentResourceType.VIDEO, oid=_dict['aid'], credential=config.credential)

    def run(self, interval: int = 120, signals: Iterable[str] = ('总结一下',)):
        """
        运行
        Args:
            interval:  任务间隔时间
            signals:  暗号列表

        Returns:
        """
        process = Process()
        process.add_thread(SessionAtGenerator(signals=signals), self.get_flow(), interval=interval)
        process.run()


class VUP(ReflectFlow):
    system: str = '你是一个Bilibili主播\n请你遵守中华人民共和国社会主义核心价值观和平台直播规范，不允许在对话中出现政治、色情、暴恐等敏感词。\n'

    async def _areact(self, _dict):
        await voice.tts_speak(_dict[self.llm_output_key])

    def get_brain(self):
        """路由分支，对弹幕和用户输入使用llm生成，另外输入方式直接输出 <input>"""
        @chain
        def route(_dict: dict):
            if _dict['type'] in {LiveInputType.danmu, LiveInputType.user}:
                return super().get_brain()
            elif _dict['type'] is {LiveInputType.direct, LiveInputType.gift}:
                return _dict['input']
        return route

    def run(
            self,
            room_id: int,
            events: Iterable[SchedulingEvent] = tuple(),
    ):
        """
        运行
        Args:
            room_id: Bilibili roomid
            events: 调度任务列表，模拟listener输出

        Returns:

        """
        # 构建
        process = Process()
        _chain = self.get_flow()
        process.add_thread(SchedulerWrapper(events=events), _chain)
        process.add_thread(LiveListener(room_id=room_id), _chain)
        process.run()

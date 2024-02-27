#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from typing import Optional, List, Iterable
from pydantic import PrivateAttr, Field

from bilibili_api import sync, Picture
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, chain, RunnableBranch

from langup import core, listener, apis, config, EventName
from langup.apis.bilibili import comment
from langup.listener.schema import LiveInputType, SchedulingEvent
from langup.chains import LLMChain
from langup.utils.utils import Continue, BanWordsFilter

logger = logging.getLogger('langup')


class VideoCommentUP(core.Langup):
    """
    模版变量:
        answer: 生成结果
        summary: 逆向得到的官方视频总结
        nickname: 发起者昵称
    """
    system: str = "你是一位B站用戶，帮助我总结视频！"
    human: str = (
        '视频内容如下\n'
        '###\n'
        '{summary}\n'
        '###'
    )
    interval: int = 10
    signals: Optional[List[str]] = ['总结一下']
    reply_temple: str = (
        '{answer}'
        '本条回复由AI生成，'
        '由@{nickname}召唤。'
    )

    @staticmethod
    @chain
    # 新版本官方提供了总结接口
    async def get_summary(_dict):
        if not any([
            signal in _dict['source_content'] for signal in _dict['signals']
        ]):
            logger.info(f"过滤,没有出现暗号:{_dict['source_content']}")
            raise Continue
        # 获取summary
        video = apis.bilibili.video.Video(aid=_dict['aid'], credential=config.auth.credential)
        logger.info('step1:获取summary')
        summary = await video.get_md_summary()
        return {'summary': summary, **_dict}

    @staticmethod
    @chain
    async def react(_dict):
        content = _dict['reply_temple'].format(answer=_dict['output'], nickname=_dict['user_nickname'])
        await comment.send_comment(text=content, type_=comment.CommentResourceType.VIDEO, oid=_dict['aid'], credential=config.auth.credential)

    def run(self):
        runer = core.RunManager(
            interval=self.interval,
            extra_inputs={'signals': self.signals, 'reply_temple': self.reply_temple},
            chain=(
                RunnablePassthrough.assign(summary=self.get_summary) |
                RunnablePassthrough.assign(output=LLMChain(self.system, self.human) | StrOutputParser()) |
                self.react
            ),
        )
        runer.single_run(listener.SessionAtListener())


class ChatUP(core.Langup):
    system: str = '你是一位聊天AI助手'
    interval: int = 5

    @staticmethod
    @chain
    async def react(_dict):
        msg_type = EventName.PICTURE if isinstance(_dict['output'], Picture) else EventName.TEXT
        await apis.bilibili.session.send_msg(config.credential, _dict['sender_uid'], msg_type.value, _dict['output'])

    def run(self):
        runer = core.RunManager(
            interval=self.interval,
            chain=(
                RunnablePassthrough.assign(output=LLMChain(self.system, self.human) | StrOutputParser())
                | self.react
            ),
        )
        runer.single_run(listener.ChatListener())


class VtuBer(core.Langup):
    """
    模版变量:
        text：输入文本描述 弹幕/礼物/定时任务...
        output：生成结果
    """
    system: str = '你是一个Bilibili主播'
    safe_system: str = """请你遵守中华人民共和国社会主义核心价值观和平台直播规范，不允许在对话中出现政治、色情、暴恐等敏感词。\n"""
    room_id: int
    audio_temple: dict = {
        LiveInputType.danmu: '{output}',
        LiveInputType.user: '{output}。',
        LiveInputType.speech: '{text}。',
        LiveInputType.gift: '感谢!{text}'
    }

    """扩展"""
    is_filter: bool = True
    schedulers: Iterable[SchedulingEvent] = Field([], description='调度事件列表')
    extra_ban_words: Optional[List[str]] = None
    _ban_word_filter: Optional[BanWordsFilter] = PrivateAttr()

    @staticmethod
    @chain
    async def react(_dict):
        audio_temple = _dict['audio_temple'][_dict['type']]
        audio_text = audio_temple.format(**_dict)
        await apis.voice.tts_speak(audio_text)

    @staticmethod
    @chain
    def filter(_dict):
        _filter: BanWordsFilter = _dict['filter']
        check_keys = ('user_name', 'text', 'answer', 'output')
        for key in check_keys:
            content = _dict.get(key)
            if kws := _filter.match(content):
                raise Continue(f'包含违禁词:{content}/{kws}')

    def run(self):
        if self.is_filter:
            self._ban_word_filter = BanWordsFilter(extra_ban_words=self.extra_ban_words)
        self.system = f"{self.safe_system}\n{self.system}"
        runer = core.RunManager(
            interval=self.interval,
            extra_inputs={'filter': self._ban_word_filter, 'audio_temple': self.audio_temple},
            chain=(
                    RunnablePassthrough.assign(
                        output=RunnableBranch(
                            (lambda x: x['type'] in {LiveInputType.danmu, LiveInputType.speech}, LLMChain(self.system, self.human) | StrOutputParser()),
                            lambda _: None
                        ) | self.filter)
                    | self.react
            ),
        )

        # 调度监听
        if self.schedulers:
            sche_listener = listener.SchedulerWrapper()
            for e in self.schedulers:
                sche_listener.scheduler.add_job(**e.get_scheduler_inputs())
            sche_listener.run()
            runer.multiple_run([listener.LiveListener(room_id=self.room_id), sche_listener])
            return
        runer.single_run(listener.LiveListener(room_id=self.room_id))

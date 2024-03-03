#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from operator import itemgetter
from typing import Optional, List, Iterable

from langchain_core.retrievers import BaseRetriever
from pydantic import PrivateAttr, Field

from bilibili_api import sync, Picture
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, chain

from langup import core, listener, apis, config
from langup.apis.bilibili import comment
from langup.listener.schema import LiveInputType, SchedulingEvent, FixedReply, EventName
from langup.chains import LLMChain
from langup.utils.utils import Continue, BanWordsFilter, KeywordsMatcher

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
                {'output': LLMChain(self.system, self.human) | StrOutputParser(), 'sender_uid': itemgetter('sender_uid')}
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
    interval: int = 0

    """扩展"""
    is_filter: bool = True
    schedulers: Iterable[SchedulingEvent] = Field([], description='调度事件列表')
    fixed_replies: Iterable[FixedReply] = Field([], description='固定回复列表列表')
    retriever: Optional[BaseRetriever] = Field(None, description='langchain检索器')
    extra_ban_words: Optional[List[str]] = None
    _ban_word_filter: Optional[BanWordsFilter] = PrivateAttr()
    _keywords_matcher: Optional[KeywordsMatcher] = PrivateAttr()

    @staticmethod
    @chain
    async def react(audio_text):
        await apis.voice.tts_speak(audio_text)

    @staticmethod
    @chain
    def filter(_dict):
        _filter: BanWordsFilter = _dict['self']._ban_word_filter
        if _dict['self'].is_filter:
            check_keys = ('user_name', 'text', 'answer', 'output')
            for key in check_keys:
                content = _dict.get(key)
                if kws := _filter.match(content):
                    raise Continue(f'包含违禁词:{content}/{kws}')
        return _dict

    @staticmethod
    @chain
    def route(_dict):
        self = _dict['self']
        if _dict['type'] in {LiveInputType.danmu, LiveInputType.user}:
            if self._keywords_matcher and (fixed_reply := self._keywords_matcher.match(_dict['text'])):
                return fixed_reply
            _chain = LLMChain(self.system, self.human) | StrOutputParser()
            if self.retriever:
                _chain = (
                    RunnablePassthrough.assign(context=_dict['text'] | self.retriever)
                    | _chain
                )
            return chain
        elif _dict['type'] is {LiveInputType.direct, LiveInputType.gift}:
            return _dict['text']
        return _dict

    def run(self):
        # 初始化
        if self.is_filter:
            self._ban_word_filter = BanWordsFilter(extra_ban_words=self.extra_ban_words)
        if self.fixed_replies:
            self._keywords_matcher = KeywordsMatcher({reply.keyword: reply.content for reply in self.fixed_replies})
        if self.retriever and 'context' not in self.human:
            self.human = "参考上下文:{context}\n" + self.human
        self.system = f"{self.safe_system}\n{self.system}"
        # 构建
        runer = core.RunManager(
            interval=self.interval,
            extra_inputs={'self': self},
            chain=(self.route | self.filter | self.react),
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

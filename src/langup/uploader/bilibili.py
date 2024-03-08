#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from operator import itemgetter
from typing import Optional, List, Iterable

from bilibili_api.dynamic import send_dynamic, BuildDynamic
from langchain.chains.base import Chain
from pydantic import PrivateAttr, Field

from bilibili_api import Picture
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, chain, RunnableConfig

from langup import core, apis, config
from langup.apis.bilibili import comment
from langup.listener.base import Listener
from langup.listener.bilibili import ChatListener, SessionAtListener, LiveListener
from langup.listener.schema import LiveInputType, SchedulingEvent, KeywordReply, EventName
from langup.utils import converts
from langup.utils.converts import summary_generator
from langup.utils.utils import Continue, BanWordsFilter, KeywordsMatcher

logger = logging.getLogger('langup.bilibili')


class VideoCommentUP(core.Langup):
    """
    模版变量:
        output: 生成结果
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
    signals: Optional[List[str]] = ['总结一下']  # 部分暗号会被屏蔽
    reply_temple: str = (
        '{output}'
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

    @staticmethod
    @chain
    async def react(_dict):
        content = _dict['reply_temple'].format(output=_dict['output'], nickname=_dict['user_nickname'])
        logger.info(f'准备发送文本:{content}')
        await comment.send_comment(text=content, type_=comment.CommentResourceType.VIDEO, oid=_dict['aid'], credential=config.auth.credential)

    def run(self):
        runer = core.RunManager(
            manager_config=self,
            extra_inputs={'signals': self.signals, 'reply_temple': self.reply_temple},
            chain=(
                RunnablePassthrough.assign(summary=self.get_summary)
                | RunnablePassthrough.assign(output=self._prompt | self.model | StrOutputParser())
                | self.react
            ),
        )
        runer.bind_listener(SessionAtListener())
        runer.forever_run()


class ChatUP(core.Langup):
    system: str = '你是一位聊天AI助手'

    @staticmethod
    @chain
    async def react(_dict):
        msg_type = EventName.PICTURE if isinstance(_dict['output'], Picture) else EventName.TEXT
        logger.debug(f"发送消息:{_dict['output']}")
        await apis.bilibili.session.send_msg(config.auth.credential, _dict['sender_uid'], msg_type.value, _dict['output'])

    def run(self):
        runer = core.RunManager(
            manager_config=self,
            chain=(
                {'output': self._prompt | self.model | StrOutputParser(), 'sender_uid': itemgetter('sender_uid')}
                | self.react
            ),
        )
        runer.bind_listener(ChatListener())
        runer.forever_run()


class DynamicUP(core.Langup):
    system: str = '你是位B站百万UP主'
    schedulers: Iterable[SchedulingEvent] = Field(description='调度事件列表')

    @staticmethod
    @chain
    async def react(_content):
        logger.info(f'发送动态:{_content}')
        await send_dynamic(BuildDynamic.create_by_args(text=_content), credential=config.auth.credential)

    def run(self):
        runer = core.RunManager(
            manager_config=self,
            chain=(
                self._prompt | self.model | StrOutputParser() | self.react
            ),
        )
        runer.forever_run()


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
    keyword_replies: Iterable[KeywordReply] = Field([], description='固定回复列表列表')
    extra_ban_words: Optional[List[str]] = None
    _ban_word_filter: Optional[BanWordsFilter] = PrivateAttr()
    _keywords_matcher: Optional[KeywordsMatcher] = PrivateAttr()

    @staticmethod
    @chain
    async def react(audio_text):
        await apis.voice.tts_speak(audio_text)

    @staticmethod
    @chain
    def filter(_dict: dict) -> dict:
        _filter: BanWordsFilter = _dict['self']._ban_word_filter
        if _dict['self'].is_filter:
            check_keys = ('user_name', 'text', 'output', 'output')
            for key in check_keys:
                content = _dict.get(key)
                if kws := _filter.match(content):
                    raise Continue(f'包含违禁词:{content}/{kws}')
        return _dict

    @staticmethod
    @chain
    def route(_dict: dict):
        self = _dict['self']
        if _dict['type'] in {LiveInputType.danmu, LiveInputType.user}:
            if self._keywords_matcher and (callback := self._keywords_matcher.match(_dict['text'])):
                if isinstance(callback, str):
                    return callback
                if isinstance(callback, Chain):
                    return callback.invoke(_dict)
            _chain = self._prompt | self.model | StrOutputParser()
            return chain
        elif _dict['type'] is {LiveInputType.direct, LiveInputType.gift}:
            return _dict['text']
        return _dict

    def model_post_init(self, __context) -> None:
        if self.is_filter:
            self._ban_word_filter = BanWordsFilter(extra_ban_words=self.extra_ban_words)
        if self.keyword_replies:
            self._keywords_matcher = KeywordsMatcher({reply.keyword: reply.content for reply in self.keyword_replies})
        self.system = f"{self.safe_system}\n{self.system}"

    def run(self):
        # 构建
        runer = core.RunManager(
            manager_config=self,
            extra_inputs={'self': self},
            chain=(self.route | self.filter | self.react)
        )
        runer.bind_listener(LiveListener(room_id=self.room_id))
        runer.forever_run()




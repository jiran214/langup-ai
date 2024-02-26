#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import logging
import time
from typing import Optional, List
from pydantic import PrivateAttr

from bilibili_api import sync, Picture
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel, RunnableLambda, chain, RunnableBranch

from langup import core, listener, apis, config
from langup.apis.bilibili import comment
from langup.apis.bilibili.live import LiveInputType
from langup.chains import LLMChain
from langup.listener.bilibili import EventName
from langup.utils.utils import Continue, BanWordsFilter

logger = logging.getLogger('langup')


class VideoCommentUP(core.Langup):
    system: str = "你是一位B站用戶，请你锐评该视频！"
    human: str = (
        '视频内容如下\n'
        '###\n'
        '{summary}\n'
        '###'
    )
    interval: int = 5
    signals: Optional[List[str]] = ['总结一下']
    reply_temple: str = (
        '{answer}'
        '本条回复由AI生成，'
        '由@{nickname}召唤。'
    )  # answer: brain回复；nickname：发消息用户昵称
    # 新版本官方提供了总结接口

    @staticmethod
    @chain
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
    interval: int = 3
    event_name_list: List[EventName] = [EventName.TEXT]

    @staticmethod
    @chain
    async def react(_dict):
        msg_type = EventName.PICTURE if isinstance(_dict['output'], Picture) else EventName.TEXT
        await apis.bilibili.session.send_msg(config.credential, _dict['sender_uid'], msg_type.value, _dict['output'])

    def run(self):
        runer = core.RunManager(
            interval=self.interval,
            chain=(
                RunnablePassthrough.assign(output=LLMChain(self.system, self.human) | StrOutputParser()) |
                self.react
            ),
        )
        runer.single_run(listener.ChatListener(event_name_list=self.event_name_list))


class VtuBer(core.Langup):
    """
    bilibili直播数字人
    监听：直播间消息
    思考：过滤、调用GPT生成文本
    反应：语音回复
    :param room_id:  bilibili直播房间号
    :param credential:  bilibili 账号认证
    :param subtitle: 是否开启字幕
    :param is_filter: 是否开启过滤
    :param user_input: 是否开启终端输入
    :param extra_ban_words: 额外的违禁词

    :param listeners:  感知
    :param concurrent_num:  并发数
    :param up_sleep: uploader 运行间隔时间
    :param listener_sleep: listener 运行间隔时间
    :param system:   人设

    :param openai_api_key:  openai秘钥
    :param openai_proxy:   http代理
    :param openai_api_base:  openai endpoint
    :param temperature:  gpt温度
    :param max_tokens:  gpt输出长度
    :param chat_model_kwargs:  langchain chatModel额外配置参数
    :param llm_chain_kwargs:  langchain chatChain额外配置参数

    :param brain:  含有run方法的类
    :param mq:  通信队列
    """
    system: str = '你是一个Bilibili主播'
    safe_system: str = """请你遵守中华人民共和国社会主义核心价值观和平台直播规范，不允许在对话中出现政治、色情、暴恐等敏感词。\n"""
    room_id: int
    audio_temple: dict = {
        LiveInputType.danmu: (
            '{user_name}说:{text}'
            '{output}'
        ),
        LiveInputType.gift: (
            '感谢!{text}'
        ),
        LiveInputType.user: (
            '{output}。'
        )
    }

    """扩展"""
    is_filter: bool = True
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
                            lambda x: x['type'] is not LiveInputType.gift,
                            LLMChain(self.system, self.human) | StrOutputParser()
                        ) | self.filter)
                    | self.react
            ),
        )
        runer.single_run(listener.LiveListener(room_id=self.room_id))

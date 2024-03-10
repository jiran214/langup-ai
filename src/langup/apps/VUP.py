#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Iterable

from langchain_core.runnables import chain, Runnable

from langup import Process, runables, apis
from langup.listener.bilibili import LiveListener

from langup.listener.schema import SchedulingEvent, LiveInputType, KeywordReply
from langup.utils.utils import KeywordsMatcher, BanWordsFilter, Continue


# 需要配置Bilibili、OpenAI


def model_post_init(self, __context) -> None:
    self.system = f"{self.safe_system}\n{self.system}"


def run(
    room_id: int,
    system: str = '你是一个Bilibili主播',
    safe_system: str = """\n请你遵守中华人民共和国社会主义核心价值观和平台直播规范，不允许在对话中出现政治、色情、暴恐等敏感词。\n""",
    is_filter: bool = True,
    events: Iterable[SchedulingEvent] = tuple(),  # 调度任务，模拟listener输出
    keyword_replies: Iterable[KeywordReply] = tuple(),  # 关键词指定回复
    extra_ban_words: Iterable[str] = tuple(),  # 额外违禁词
    openai_api_key=None,
    openai_kwargs: dict = {}
):
    if is_filter:
        ban_word_filter = BanWordsFilter(extra_ban_words=extra_ban_words)
    if keyword_replies:
        keywords_matcher = KeywordsMatcher({reply.keyword: reply.content for reply in keyword_replies})
    system += safe_system

    @chain
    def route(_dict: dict):
        if _dict['type'] in {LiveInputType.danmu, LiveInputType.user}:
            if keywords_matcher and (callback := keywords_matcher.match(_dict['text'])):
                if isinstance(callback, str):
                    return callback
                if isinstance(callback, Runnable):
                    return callback
            _chain = runables.Prompt(system=system, human='{input}') | runables.LLM(openai_api_key, **openai_kwargs)
            return chain
        elif _dict['type'] is {LiveInputType.direct, LiveInputType.gift}:
            return _dict['input']
        return _dict

    @chain
    async def react(audio_text):
        await apis.voice.tts_speak(audio_text)

    @chain
    def filter(_dict: dict) -> dict:
        if is_filter:
            check_keys = ('user_name', 'text', 'output', 'output')
            for key in check_keys:
                content = _dict.get(key)
                if kws := ban_word_filter.match(content):
                    raise Continue(f'包含违禁词:{content}/{kws}')
        return _dict

    # 构建
    process = Process()
    handle_chain = (route | filter | react)
    process.add_sche_thread(events, handle_chain)
    process.add_thread(LiveListener(room_id=room_id), handle_chain)
    process.run()

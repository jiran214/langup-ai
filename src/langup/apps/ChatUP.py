#!/usr/bin/env python
# -*- coding: utf-8 -*-
from operator import itemgetter

from bilibili_api.session import send_msg, EventType
from langchain_core.runnables import chain

from langup import config, runables, Process
from langup.listener.bilibili import ChatListener

# 需要配置Bilibili
config.set_bilibili_cookies(sessdata='', buvid3='', bili_jct='')


@chain
async def react(_dict):
    await send_msg(config.credential, _dict['sender_uid'], EventType.TEXT, _dict['output'])


def run(system, openai_api_key=None, openai_kwargs: dict = {}):
    process = Process()
    _chain = (
        {
            'output':
                runables.Prompt(system=system, human='{input}')
                | runables.LLM(openai_api_key, model_name="gpt-3.5-turbo", **openai_kwargs),
            'sender_uid': itemgetter('sender_uid')}
        | react
    )
    process.add_thread(ChatListener(), _chain)
    process.run()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Literal
from langchain_core.runnables import chain, RunnableLambda

from langup import runables, Process
from langup.listener.bilibili import ChatListener

from langup import apis
from langup.listener.user import ConsoleListener, SpeechListener
from langup.utils import utils


# 语音实时识别回复
# 语音识别参数见config.convert


_user_listener_map = {
    'console': ConsoleListener,
    'speech': SpeechListener
}


@chain
async def react(_content):
    utils.format_print(f"AI: {_content}", color='green')
    await apis.voice.tts_speak(audio_txt=_content)


def run(system, openai_api_key, listen: Literal['console', 'speech'], openai_kwargs: dict):
    process = Process()
    user_listener = _user_listener_map[listen]()
    _chain = (
             runables.Prompt(system=system, human='{input}')
             | runables.LLM(openai_api_key, model_name="gpt-3.5-turbo", **openai_kwargs)
             | react
             | RunnableLambda(user_listener.user_event.set)
    )
    process.add_thread(ChatListener(), _chain)
    user_listener.user_event.set()
    process.run()

import datetime
import time
import typing
from typing import List

from langchain.chains.base import Chain

from langup import base, config, listener
from langup import reaction
from langup.brain.chains import llm
from langup.utils import enums


class CommentAtReplyUP(base.Uploader):
    """
    监听：@消息
    思考：调用GPT回复消息
    反应：评论该消息
    """
    default_system = "你是一个会评论视频的UP主"

    temple = (
        '{answer}。'
        '本条回复由AI生成，'
        '由@{nickname}召唤。'
    )  # answer: brain回复；nickname：发消息用户昵称

    def __init__(self, system: str):
        brain = llm.get_simple_chat_chain(system=system or self.default_system)
        super().__init__([listener.SessionAtListener], brain=brain)

    def execute_sop(self, schema: listener.SessionAtListener.Schema) -> reaction.CommentReaction:
        prompt = schema.source_content
        answer = self.brain.run(prompt)
        content = self.temple.format(
            answer=answer,
            nickname=schema.user_nickname
        )
        return reaction.CommentReaction(
            aid=schema.aid,
            content=content
        )


class VtuBer(base.Uploader):
    audio_temple = {
        enums.LiveInputType.danmu: (
            '{user_name}说:{text}？'
            '{answer}。'
        ),
        enums.LiveInputType.gift: (
            '感谢!{text}'
        )
    }

    def __init__(self, system: str, room_id: int, openai_api_key=None):
        brain = llm.get_simple_chat_chain(
            system=system or self.default_system,
            openai_api_key=openai_api_key,
            chat_model_kwargs={'max_tokens': 150}
        )
        listener.LiveListener.room_id = room_id
        super().__init__([listener.LiveListener], brain=brain)

    def execute_sop(self, schema: listener.LiveListener.Schema) -> reaction.TTSSpeakReaction:
        t0 = time.time()
        audio_kwargs = {**schema}
        audio_temple = self.audio_temple[schema['type']]
        if schema['type'] is not enums.LiveInputType.gift:
            prompt = schema['text']
            audio_kwargs['answer'] = self.brain.run(prompt)
        audio_txt = audio_temple.format(
            **audio_kwargs
        )

        schema['type'] = schema['type'].value
        rcd = base.Record(
            schema=schema,
            time_cost=str(time.time()-t0).split('.')[0],
            created_time=str(datetime.datetime.now()),
            react_kwargs={'audio_txt': audio_txt}
        )
        if 'print' in config.record['console']:
            rcd.print()
        if 'file' in config.record['console']:
            rcd.save_file(path=f"{config.record['file_path']}{self.__class__.__name__}Record.txt")
        return reaction.TTSSpeakReaction(audio_txt=audio_txt, block=True)

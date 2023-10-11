import datetime
import time
import typing
from typing import List

from langchain.chains.base import Chain

from langup import base, config, listener
from langup import reaction
from langup.brain.chains import llm
from langup.utils import enums, filters


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
    """
    监听：直播间消息
    思考：过滤、调用GPT生成文本
    反应：语音回复
    """

    safe_system = """请你遵守中华人民共和国社会主义核心价值观，不允许在对话中出现政治、色情、暴恐等敏感词。\n"""

    audio_temple = {
        enums.LiveInputType.danmu: (
            '{user_name}说:{text}？'
            '{answer}。'
        ),
        enums.LiveInputType.gift: (
            '感谢!{text}'
        )
    }

    def __init__(
            self,
            room_id: int,
            system: str = typing.Optional[None],
            brain: Chain = typing.Optional[None],
            openai_api_key=None,
            concurrent_num=1
    ):
        assert system or brain, 'system、brain至少提供一个'
        brain = brain or llm.get_simple_chat_chain(
            system=self.safe_system + system or self.default_system,
            openai_api_key=openai_api_key,
            chat_model_kwargs={'max_tokens': 150}
        )
        listener.LiveListener.room_id = room_id
        super().__init__([listener.LiveListener], brain=brain, concurrent_num=concurrent_num)
        self.ban_word_filter: filters.BanWordsFilter = filters.BanWordsFilter()

    def execute_sop(self, schema: listener.LiveListener.Schema) -> typing.Union[None, reaction.TTSSpeakReaction]:
        audio_kwargs = {**schema}
        audio_temple = self.audio_temple[schema['type']]
        if schema['type'] is not enums.LiveInputType.gift:
            prompt = schema['text']
            if words := self.ban_word_filter.match(prompt):
                self.logger.warning(f'包含违禁词-{prompt}-{words}')
                return
            audio_kwargs['answer'] = self.brain.run(prompt)
        audio_txt = audio_temple.format(
            **audio_kwargs
        )
        if words := self.ban_word_filter.match(audio_txt):
            self.logger.warning(f'包含违禁词-{audio_txt}-{words}')
            return
        schema['type'] = schema['type'].value
        return reaction.TTSSpeakReaction(audio_txt=audio_txt, block=True)

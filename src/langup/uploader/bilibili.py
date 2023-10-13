import typing

from bilibili_api import Credential

from langup import base, config, listener, BrainType
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

    def __init__(self, *args, **kwargs):
        super().__init__([listener.SessionAtListener], *args, **kwargs)

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

    safe_system = """请你遵守中华人民共和国社会主义核心价值观和平台直播规范，不允许在对话中出现政治、色情、暴恐等敏感词。\n"""

    audio_temple = {
        enums.LiveInputType.danmu: (
            '{user_name}说:{text}？'
            '{answer}。'
        ),
        enums.LiveInputType.gift: (
            '感谢!{text}'
        ),
        enums.LiveInputType.user: (
            '{answer}。'
        )
    }

    def __init__(
            self,
            room_id: int,
            credential: Credential,
            is_filter=True,
            extra_ban_words: typing.List[str]=None,
            user_input=False,
            max_tokens=150,
            *args,
            **kwargs
    ):
        """
        bilibili直播数字人
        :param room_id:  bilibili房间号
        :param is_filter: 是否开启过滤
        :param user_input: 是否开启终端输入
        :param extra_ban_words: 额外的违禁词

        :param listeners:  感知
        :param concurrent_num:  并发数
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
        listener.LiveListener.room_id = room_id
        listener.LiveListener.credential = credential
        listeners = [listener.LiveListener]
        if user_input:
            listeners.append(listener.ConsoleListener)
        self.ban_word_filter: filters.BanWordsFilter = filters.BanWordsFilter(extra_ban_words=extra_ban_words) \
            if is_filter else None
        super().__init__(listeners, max_tokens=max_tokens, *args, **kwargs)

    def console_2_live(self, schema):
        return {
            'text': schema.user_input,
            'type': enums.LiveInputType.user
        }

    def execute_sop(
            self,
            schema: typing.Union[dict, listener.ConsoleListener.Schema]
    ) -> typing.Union[None, reaction.TTSSpeakReaction]:
        if isinstance(schema, listener.ConsoleListener.Schema):
            schema = self.console_2_live(schema)
        audio_kwargs = {**schema}
        audio_temple = self.audio_temple[schema['type']]
        if schema['type'] is not enums.LiveInputType.gift:
            prompt = schema['text']
            if self.ban_word_filter and (words := self.ban_word_filter.match(prompt)):
                self.logger.warning(f'包含违禁词-{prompt}-{words}')
                return
            audio_kwargs['answer'] = self.brain.run(prompt)
        audio_txt = audio_temple.format(
            **audio_kwargs
        )
        if self.ban_word_filter and (words := self.ban_word_filter.match(audio_txt)):
            self.logger.warning(f'包含违禁词-{audio_txt}-{words}')
            return
        schema['type'] = schema['type'].value
        return reaction.TTSSpeakReaction(audio_txt=audio_txt, block=True)

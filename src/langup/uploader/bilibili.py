import typing
from typing import Optional, Union, Literal

from bilibili_api import Credential, sync

from langup import base, config, listener, BrainType
from langup import reaction
from langup.api.bilibili.video import Video
from langup.brain.chains import llm
from langup.utils import enums, filters, converts
from langup.utils.utils import Record


class VideoCommentUP(base.Uploader):
    """
    监听：@消息
    思考：调用GPT回复消息
    反应：评论该消息
    """
    SLEEP = 60 * 5  # 5分钟响应一次
    default_system = "你是一个会评论视频B站观众，请总结视频并做出评论"
    default_signals = ['总结一下']
    prompt_temple = (
        '视频内容如下\n'
        '标题:{title}'
        '{summary}'
    )

    reply_temple = (
        '{answer}。'
        '本条回复由AI生成，'
        '由@{nickname}召唤。'
    )  # answer: brain回复；nickname：发消息用户昵称

    def __init__(
            self,
            credential: Optional[Credential] = None,
            model_name='gpt-3.5-turbo',
            signals=None,

            limit_video_seconds: Optional[int] = None,

            limit_token: Union[int, str, None] = None,
            limit_length: Optional[int] = None,
            compress_mode: Literal['random', 'left'] = 'random',
            *args, **kwargs
    ):
        self.signals = signals or self.default_signals
        if credential:
            config.credential = credential
        self.limit_video_seconds = limit_video_seconds
        assert config.credential, '请提供认证config.credential'
        self.summary_generator = converts.SummaryGenerator(
            limit_token=limit_token,
            limit_length=limit_length,
            compress_mode=compress_mode
        )
        self.aid_record_map = {
            int(record_dict['listener_kwargs']['aid']): Record(**record_dict) for record_dict in self.query()
        }

        listener.SessionAtListener.credential = credential
        chat_model_kwargs = {'model_name': model_name}
        super().__init__([listener.SessionAtListener], chat_model_kwargs=chat_model_kwargs, *args, **kwargs)

    async def execute_sop(self, schema: listener.SessionAtListener.Schema) -> Optional[reaction.CommentReaction]:
        self.logger.info(f'step0:收到schema:{schema.source_content}')
        if not any([
            signal in schema.source_content for signal in self.signals
        ]):
            self.logger.info(f'过滤,没有出现暗号:{schema.source_content}')
            return
        if schema.aid in self.aid_record_map:
            self.logger.info(f'过滤,aid:{schema.aid}已经回复过')
            return

        # 获取summary
        video = Video(aid=schema.aid, credential=config.credential)
        video_content_list = await converts.Audio2Text.from_bilibili_video(video)
        view = video.info
        self.logger.info('step1:获取summary')

        # 过滤
        self.logger.info('step2:过滤')
        if self.limit_video_seconds and view.duration > self.limit_video_seconds:
            self.logger.info(f'过滤,视频时长超出限制:{view.duration}')
            return
        if not video_content_list:
            self.logger.error('查找字幕资源失败')
            return
        summary = self.summary_generator.generate(video_content_list)

        # 请求GPT
        prompt = self.prompt_temple.format(summary=summary, title=view.title)
        self.logger.info(f'step3:请求GPT-prompt:{prompt[:10]}...{prompt[-10:]}')
        answer = self.brain.run(prompt)
        content = self.reply_temple.format(
            answer=answer,
            nickname=schema.user_nickname
        )
        self.aid_record_map[schema.aid] = None
        self.logger.info('end')
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
    default_system = '你是一个Bilibili主播'

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
            credential: Credential=None,
            is_filter=True,
            extra_ban_words: typing.List[str] = None,
            user_input=False,
            max_tokens=150,
            *args,
            **kwargs
    ):
        """
        bilibili直播数字人
        :param room_id:  bilibili房间号
        :param credential:  bilibili 账号认证
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
        if credential:
            config.credential = credential
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

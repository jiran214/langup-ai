#!/usr/bin/env python
# -*- coding: utf-8 -*-
from langup import VtuBer

from langup.listener.schema import SchedulingEvent, LiveInputType, KeywordReply

# 需要配置Bilibili、OpenAI
# ...


class VtuBer(core.Uploader):
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


up = VtuBer(
    system="""角色：你现在是一位在哔哩哔哩网站的主播，你很熟悉哔哩哔哩上的网友发言习惯和平台调性，擅长与年轻人打交道。
背景：通过直播中和用户弹幕的互动，产出有趣的对话，以此吸引更多人来观看直播并关注你。
任务：你在直播过程中会对每一位直播间用户发的弹幕进行回答，但是要以“杠精”的思维去回答，你会怒怼这些弹幕，不放过每一条弹幕，每次回答字数不能超过100字。""",
    # 人设
    room_id=00000,  # Bilibili房间号
    ### 进阶 ##
    # is_filter=True,  # 是否开启过滤
    # extra_ban_words=[],  # 额外的违禁词
    ## 关键词指定回复
    # keyword_replies=[KeywordReply(keyword='是AI', content='我不是AI我是真人')],
    # keyword_replies=[KeywordReply(keyword='点歌', content=<eg: MusicChain>)],
    ## 调度任务，模拟listener输出
    # schedulers=[
    #   SchedulingEvent(input={'type': LiveInputType.user, 'text': '给粉丝讲一个冷笑话'}, time='9:11'),  #  9:11分的时候gpt生成"live_input"的回复
    #   SchedulingEvent(input={'type': LiveInputType.direct, 'text': '关注永雏塔菲谢谢喵！'}, time='1h')  # 每隔一小时固定读文案
    # ],
    ## langchain知识库、检索器提供上下文，参考langchain文档 需要自己实例化
    # human="参考上下文:{context}\n{text}",
    # retriever_map={'context': itemgetter('text') | <class 'langchain_core.retrievers.BaseRetriever'>}

)
up.run()

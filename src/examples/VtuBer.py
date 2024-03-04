#!/usr/bin/env python
# -*- coding: utf-8 -*-
from langup import VtuBer

from langup import SchedulingEvent, LiveInputType, KeywordReply

# 需要配置Bilibili、OpenAI
# ...

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
    # keyword_replies=[KeywordReply(keyword='点歌', content=<Chain: MusicChain>)],
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

import json

from bilibili_api import sync
from langup import Audio2Text
from langup.api.bilibili.video import Video
from langup.brain.chains import llm

brain = llm.get_chat_chain(
    system="",
    openai_api_key='xxx',
    openai_proxy='http://127.0.0.1:7890'
)

summary_temple = """
请你帮我总结这个来自B站的视频，并提取高频和精华关键词，不允许在总结的内容中提到关键词。
###
标题:{title}
内容:
{content}
###
输出要求：
- 响应格式为json格式，键值为summary、keywords。keywords为关键词数组，不要输出与json无关的内容
- 关键词不超过10个
- 使用中文输出总结的内容和关键词。
"""

# v = Video(bvid='BV1Nh4y1a7CK')
# content_list = sync(Audio2Text.from_bilibili_video(v))
# video_content = '\n'.join(content_list)
# view = v.info
# prompt = summary_temple.format(title=view.title, content=video_content)
# resp_text = brain.run(prompt)
# print(resp_text)
# data_dict = json.loads(resp_text)
data_dict = {"summary": "这个视频主要讲述了爱自己的重要性，以及不要被别人的看法限制自己的能力。作者强调要积极向上，不要害怕失败，不要拘泥于过去和后悔。他还强调了创造力和真实性的重要性，以及不要被社会规则束缚。关键词包括自信、积极向上、失败、创造力、真实性、社会规则。",
             "keywords": ["自信", "积极向上", "失败", "创造力", "真实性", "社会规则"]}
kws, summary = data_dict['keywords'], data_dict['summary']


rap_temple = (
    "You are a Chinese rap artist participating in a highly anticipated rap battle. "
    "Your opponent is known for their quick-witted rhymes and clever wordplay. "
    "Your challenge is to write a set of rap lyrics that not only showcase your own lyrical prowess "
    "but also outshine your opponent's skills. Your rap must contain at least three different rhyming schemes, "
    "reference a current event, and include a creative metaphor or simile.\n\n"
    "你需要在每一句中文歌词后加上拼音，让你更好理解韵律。"
    "我将给你的创作提供一些视频、文字素材、韵脚(rhymes)，你必须根据这些素材创作，主旨统一，歌词震人心魄！\n"
    "标题: {title}\n"
    "摘要: {summary}\n"
    "韵脚1:自信 自禁 是近 自尽 置信\n"
    "韵脚2:失败 之外 失态 丝带 之爱 失在\n"
    "韵脚3:社会 撤退 热泪 各位 个位\n"
    "韵脚4:像套戏 创造力 唱到腻 上傲气 上峭壁 壮傲气\n\n"
    "你创作出的rap输出文字格式精美，需要带一个歌名，请开始你的创作！"
    # "评价: {comment}"
)


prompt = rap_temple.format(title='如何像kanye爱kanye那样爱你自己', summary=summary)
rap = brain.run(prompt)
print(rap)
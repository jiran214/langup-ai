# <center> Langup
<p align='center'>
   llm + bot
<br>
<br>
    🚀AGI时代通用机器人🚀
</p>

## 安装
环境：python>=3.8

```shell
# 建议使用python虚拟环境
pip install langup==0.0.10
```

## 快速开始
- 安装完成后，新建xxx.py文件参考以下代码
- 所有代码示例 src/examples可见

<details>
    <summary> 前置步骤 </summary>

OpenAI配置
```python
# 1.手动传入
from langup import config
config.set_openai_config(openai_api_key='xxx', model_name='gpt-3.5-turbo')  # langchain.ChatOpenAI 参数

# 2.环境变量方式 见下
# openai_config更多参数不做解释
```

Bilibili配置
```python
from langup import config, get_cookies
# 1.手动传入：登录Bilibili 从浏览器获取cookie:https://nemo2011.github.io/bilibili-api/#/get-credential
config.set_bilibili_config(sessdata='xxx', buvid3='xxx', bili_jct='xxx', dedeuserid='xxx', ac_time_value='xxx')

# 2.自动读取浏览器的缓存cookie
# config.auth.set_bilibili_config(**get_cookies(domain_name='bilibili.com', browser='edge'))

# 3.环境变量方式 见下
```

代理配置
```python
# 系统内openai设置代理
from langup import config
config.set_openai_config(openai_api_key='xxx', model_name='gpt-3.5-turbo', openai_proxy='http://xxx')

# 系统内部全局(包括bilibili_api)设置代理
# config.proxy = 'http://xxx'

# 系统外设置系统代理
...
```

环境变量设置
- 通过环境变量设置参数：工作目录下新建 .env 文件
  ```text
  OPENAI_API_KEY=xxx
  sessdata=xxx
  buvid3=xxx
  ```

</details>

<details>
    <summary>Bilibili 直播自动回复</summary>

```python
from langup import VtuBer

# from langup import SchedulingEvent, LiveInputType, KeywordReply

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
    ## 调度任务
    # schedulers=[
    #   SchedulingEvent(live_type=LiveInputType.user, live_input='给粉丝讲一个冷笑话',time='9:11'),  # 9:11分的时候gpt生成"live_input"的回复
    #   SchedulingEvent(live_type=LiveInputType.direct, live_input='关注永雏塔菲谢谢喵！',time='1h')  # 每隔一小时固定读固定文案
    # ],
    ## langchain知识库、检索器提供上下文，参考langchain文档 需要自己实例化
    # human="参考上下文:{context}\n{text}",
    # context_map={'context': <class 'langchain_core.contexts.Basecontext'>}
)
up.run()
```
</details>

<details>
    <summary>视频@回复机器人</summary>
<br>

```python
from langup import VideoCommentUP

# 需要配置Bilibili、OpenAI
# ...

up = VideoCommentUP(
    system="你是一位B站资深二次元爱好者，请你锐评我给你的视频！",
    signals=['总结一下', '评论一下'],
    reply_temple=(
        '{answer}'
        '本条回复由AI生成，'
        '由@{nickname}召唤。'
    )
)
up.run()
```
注: 新版本使用了B站AI总结的接口
</details>

<details>
    <summary>B站私信聊天机器人</summary>
<br>

```python
from langup import ChatUP

# 需要配置Bilibili、OpenAI
# ...

ChatUP(system='你是一位聊天AI助手').run()
```
</details>

<details>
    <summary>B站私信聊天机器人</summary>
<br>

```python
from langup import DynamicUP

# 需要配置Bilibili、OpenAI
# ...

from langup.listener.schema import SchedulingEvent
from langup import DynamicUP


DynamicUP(
  schedulers=[
    SchedulingEvent(input='请感谢大家的关注！', time='10m'),  # 每隔10分钟生成一条动态
    SchedulingEvent(input='请感谢大家的关注！', time='0:36')  # 0:36 生成一条动态
  ]
).run()
```
</details>

<details>
    <summary>实时语音交互助手</summary>

```python
from langup import UserInputReplyUP

# 需要配置OpenAI
# ...

# 语音实时识别回复
# 语音识别参数见config.convert
UserInputReplyUP(system='你是一位AI助手', listen='speech').run() 
```
</details>

<details>
    <summary>终端交互助手</summary>
<br>

```python
from langup import UserInputReplyUP, config

# 需要配置OpenAI
# ...

# 终端回复
UserInputReplyUP(system='你是一位AI助手', listen='console').run()
```
</details>


<details>
    <summary>进阶</summary>
</details>

替换llm模型
定时任务
关键词触发
注入知识
配置langchain callback
设置llm缓存

<details>
    <summary>其它</summary>

- 国内环境需要设置代理 `langup.config.set_openai_config(openai_proxy='http://127.0.0.1:7890')`
- 查看debug日志方式 `langup.set_logger()`
- 查看langchain日志方式 `langup.set_langchain_debug()`
</details>


更多机器人开发中...

## 最后
- 感谢项目依赖的开源
  - langchain https://github.com/langchain-ai/langchain
  - Bilibili API https://github.com/nemo2011/bilibili-api
  - 必剪API https://github.com/SocialSisterYi/bcut-asr
- 禁止滥用本库，使用本库请遵守各平台安全规范，可通过提示词、过滤输入等方式
- 示例代码仅供参考，尤其是提示词编写没有必要一样
- 代码可能异常，对于改进和报错问题可以在写在issues

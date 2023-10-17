# <center> Langup
<p align='center'>
   llm + bot
<br>
<br>
    🚀AGI时代通用机器人🚀
</p>

## 安装
环境：python>=3.8

- 方式一(暂时不可用)
  ```shell
  pip install langup
  ```
- 方式二(建议使用python 虚拟环境)
  ```shell
  git clone https://github.com/jiran214/langup-ai.git
  cd langup-ai/
  python -m pip install –upgrade pip
  python -m pip install -r requirements.txt
  ```
  

## 快速开始
安装完成后，新建.py文件复制以下代码（注意：采用方式二安装时，可以在src/下新建）
<details>
    <summary>Bilibili 直播数字人</summary>
<br>

```python
from langup import Credential, config, VtuBer

# config.proxy = 'http://127.0.0.1:7890'
up = VtuBer(
    system="""角色：你现在是一位在哔哩哔哩网站的主播，你很熟悉哔哩哔哩上的网友发言习惯和平台调性，擅长与年轻人打交道。
背景：通过直播中和用户弹幕的互动，产出有趣的对话，以此吸引更多人来观看直播并关注你。
任务：你在直播过程中会对每一位直播间用户发的弹幕进行回答，但是要以“杠精”的思维去回答，你会怒怼这些弹幕，不放过每一条弹幕，每次回答字数不能超过100字。""",  # 人设
    room_id=00000,  # Bilibili房间号
    credential = Credential(**{
        "sessdata": 'xxx',
        "bili_jct": 'xxx',
        "buvid3": "xxx"
    }),
    openai_api_key="""xxx""",  # 同上
    is_filter=True,  # 是否开启过滤
    extra_ban_words=None,  # 额外的违禁词
    concurrent_num=2  # 控制回复弹幕速度
)
up.loop()
```

```text
"""
bilibili直播数字人参数：
:param room_id:  bilibili直播房间号
:param credential:  bilibili 账号认证
:param is_filter: 是否开启过滤
:param user_input: 是否开启终端输入
:param extra_ban_words: 额外的违禁词

...见更多配置
"""
```

</details>

<details>
    <summary>视频@回复机器人</summary>
<br>

```python
from langup import config, Credential, VideoCommentUP

# config.proxy = 'http://127.0.0.1:7890'
up = VideoCommentUP(
    credential=Credential(**{
        "sessdata": "xxx",
        "bili_jct": "xxx",
        "buvid3": "xxx"
    }),  # 登录Bilibili 从浏览器获取cookie:https://nemo2011.github.io/bilibili-api/#/get-credential
    system="你是一个会评论视频B站用户，请根据视频内容做出总结、评论",
    signals=['总结一下'],
    openai_api_key='xxx',
    model_name='gpt-3.5-turbo'
)
up.loop()
```

```text
"""
视频下at信息回复机器人
:param credential: bilibili认证
:param model_name: openai MODEL
:param signals:  at暗号列表 （注意：B站会过滤一些词）
:param limit_video_seconds: 过滤视频长度 
:param limit_token: 请求GPT token限制（默认为model name）
:param limit_length: 请求GPT 字符串长度限制
:param compress_mode: 请求GPT 压缩过长的视频文字的方式
    - random：随机跳跃筛选
    - left：从左到右
    
:param up_sleep: 每次回复的间隔运行时间(秒)
:param listener_sleep: listener 每次读取@消息的间隔运行时间(秒)
...见更多配置
"""
```
</details>

<details>
    <summary>超简单命令端交互机器人</summary>
<br>

```python
from langup import config, ConsoleReplyUP
# config.proxy = 'http://127.0.0.1:7890'
ConsoleReplyUP(openai_api_key = """xxx""").loop()  # 一行搞定
```
</details>

<details>
    <summary>更多配置（可忽略）</summary>
<br>

```text
"""
Uploader 所有公共参数：
:param listeners:  感知
:param concurrent_num:  并发数
:param up_sleep: uploader 间隔运行时间 
:param listener_sleep: listener 间隔运行时间 
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
```

全局配置文件：
```python
"""
langup/config.py
修改方式：
form langup import config
config.xxx = xxx
"""
import os
from typing import Union

credential: Union['Credential', None] = None
work_dir = './'

tts = {
    "voice": "zh-CN-XiaoyiNeural",
    "rate": "+0%",
    "volume": "+0%",
    "voice_path": 'voice/'
}

log = {
    "console": ["print"],  # print打印生成信息, file文件存储生成信息
    "file_path": "logs/"
}

convert = {
    "audio_path": "audio/"
}

root = os.path.dirname(__file__)
openai_api_key = None  # sk-...
openai_api_base = None  # https://{your_domain}/v1
proxy = None  # 代理
debug = True
```
</details>
更多机器人开发中...
<br>

注意：
- api_key可自动从环境变量获取
- 国内环境需要设置代理或者openai_api_base 推荐config.proxy='xxx'全局设置，避免设置局部代理导致其它服务不可用
- Bilibili UP都需要 认证信息  # 登录Bilibili 从浏览器获取cookie:https://nemo2011.github.io/bilibili-api/#/get-credential

## 架构设计
<img align="center" width="50%" height="auto" src="https://cdn.nlark.com/yuque/0/2023/png/32547973/1697191309882-31b247a5-86d2-485c-8c2a-f62d185be1fd.png" >

## TodoList
- Uploader
  - Vtuber
    - [X] 基本功能
    - [X] 违禁词
    - [X] 并发
  - VideoCommentUP
    - [X] 基本功能
  - ConsoleReplyUP
    - [X] 基本功能
- Listener
- Reaction
- 其它
  - 日志记录

## 提示
<details>
    <summary>国内访问ChatGPT方式：Vercel反向代理openai api</summary>
    具体见 <a href="https://github.com/jiran214/proxy" target="_blank">https://github.com/jiran214/proxy</a>
    <br>
    <img src="https://camo.githubusercontent.com/5e471e99e8e022cf454693e38ec843036ec6301e27ee1e1fa10325b1cb720584/68747470733a2f2f76657263656c2e636f6d2f627574746f6e" alt="Vercel" data-canonical-src="https://vercel.com/button" style="max-width: 100%;"> 
<br>
<br>
</details>

## 最后
- 感谢项目依赖的开源
  - langchain https://github.com/langchain-ai/langchain
  - Bilibili API https://github.com/nemo2011/bilibili-api
  - 必剪API https://github.com/SocialSisterYi/bcut-asr
- 禁止滥用本库，使用本库请遵守各平台安全规范，可通过提示词、过滤输入等方式
- 示例代码仅供参考，尤其是提示词编写没有必要一样
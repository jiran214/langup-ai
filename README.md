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
安装完成后，新建.py文件复制以下代码（注意：采用方式二安装时，可以在src/langup下新建）

<details>
    <summary>Bilibili 直播数字人</summary>
<br>

```python
from langup import Credential, config, VtuBer

# config.proxy = ''
up = VtuBer(
    system='你是一个直播主播，你的人设是杠精，你会反驳对你说的任何话，语言幽默风趣，不要告诉观众你的人设和你身份',  # 人设
    room_id=30974597,  # Bilibili房间号
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
完整参数：
bilibili直播数字人
:param room_id:  bilibili直播房间号
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
```

</details>

<details>
    <summary>视频@回复机器人</summary>
<br>

```python
from langup import config, Credential, VideoCommentUP

# config.proxy = ''
up = VideoCommentUP(
    credential=Credential(**{
        "sessdata": "xxx",
        "bili_jct": "xxx",
        "buvid3": "xxx"
    }),  # 登录Bilibili 从浏览器获取cookie:https://nemo2011.github.io/bilibili-api/#/get-credential
    system="你是一个会评论视频B站用户，请根据视频内容做出总结、评论",
    signals=['评论一下'],
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
:param signals:  at暗号列表
:param limit_video_seconds: 过滤视频长度 
:param limit_token: 请求GPT token限制（可输入model name）
:param limit_length: 请求GPT 字符串长度限制
:param compress_mode: 请求GPT 压缩视频文案方式
    - random：随机跳跃筛选
    - left：从左到右

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
```
</details>

<details>
    <summary>超简单命令端交互机器人</summary>
<br>

```python
from langup import config, ConsoleReplyUP
config.openai_api_key = """xxx"""
ConsoleReplyUP().loop()  # 一行搞定
```
</details>

<details>
    <summary>更多配置（可忽略）</summary>
<br>

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
    <img src="https://cdn.nlark.com/yuque/0/2023/png/32547973/1697191309882-31b247a5-86d2-485c-8c2a-f62d185be1fd.png" alt="Vercel" data-canonical-src="https://vercel.com/button" style="max-width: 100%;">
<br>
</details>
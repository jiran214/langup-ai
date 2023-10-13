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

# 登录Bilibili 从浏览器获取cookie:https://nemo2011.github.io/bilibili-api/#/get-credential
config.credential = Credential(**{
    # "sessdata": '',
    # "bili_jct": '',
    # "buvid3": '',
    # "dedeuserid": '',
    # "ac_time_value": ''
})

# config.openai_api_key = 'xxx'  # 同下，配置一次即可
# config.proxy = 'http://127.0.0.1:7890'  # 国内访问需要代理，也可以通过Vercel、Cloudfare反代
# config.openai_baseurl = '...'  # 不了解的跳过


up = VtuBer(
    system='你是一个直播主播，你的人设是杠精，你会反驳对你说的任何话，语言幽默风趣，不要告诉观众你的人设和你身份',  # 人设
    room_id=30974597,  # Bilibili房间号
    openai_api_key="""xxx""",  # 同上
    is_filter=True,  # 是否开启过滤
    extra_ban_words=None,  # 额外的违禁词
    concurrent_num=1  # 并发数 1-3
)
up.loop()
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

更多机器人开发中...

## 架构设计
<img align="center" width="100%" height="auto" src="https://github.com/jiran214/langup-ai/blob/master/docs/jiagou.png?raw=true" >

## TodoList
- Uploader
  - Vtuber
    - [X] 基本功能
    - [X] 违禁词
    - [X] 并发
- Listener
- Reaction
- 其它
  - 日志记录

## 小提示
<details>
    <summary>国内访问ChatGPT：Vercel反向代理openai api</summary>
    <img src="https://camo.githubusercontent.com/5e471e99e8e022cf454693e38ec843036ec6301e27ee1e1fa10325b1cb720584/68747470733a2f2f76657263656c2e636f6d2f627574746f6e" alt="Vercel" data-canonical-src="https://vercel.com/button" style="max-width: 100%;">
    具体见 <a href="https://github.com/jiran214/proxy" target="_blank">https://github.com/jiran214/proxy</a>
<br>
</details>
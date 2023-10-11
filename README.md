# Langup
<p align='center'>
   langup = llm + bot
<br>
<br>
    AGI时代通用机器人
</p>

## 安装
环境：python>=3.8

- 方式一
  ```shell
  pip install langup
  ```
- 方式二(建议使用python 虚拟环境)
  ```shell
  git clone https://github.com/jiran214/langup-ai/tree/master
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
    openai_api_key="""xxx"""  # 同上
)
up.loop()
```
</details>

更多机器人开发中...

# 架构
<img align="center" width="100%" height="auto" src="https://github-production-user-asset-6210df.s3.amazonaws.com/50035229/250274252-7f07a95e-b5aa-4dd8-90e7-5fb3bfb863c7.svg" >

# TodoList
- Uploader
  - Vtuber
    - [X] 基本功能
- Listener
- Reaction
- 其它

# 小提示
<details>
    <summary>国内访问ChatGPT：Vercel反向代理openai api</summary>
    见<a href="https://github.com/jiran214/proxy" target="_blank">
<br>
</details>
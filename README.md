# langup
后AGI时代社交网络机器人

## 安装
```shell
pip install langup
```

## 快速开始
```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/6 14:08
# @Author  : 雷雨
# @File    : Vtuber.py
# @Desc    :
from langup import Credential, config, VtuBer

# 登录Bilibili 从浏览器获取cookie:https://nemo2011.github.io/bilibili-api/#/get-credential
config.credential = Credential(**{
    # "sessdata": '',
    # "bili_jct": '',
    # "buvid3": '',
    # "dedeuserid": '',
    # "ac_time_value": ''
})

config.openai_api_key = """xxx"""

up = VtuBer(
    system='你是一个直播主播，你的人设是杠精，你会反驳对你说的任何话，语言幽默风趣，不要告诉观众你的人设和你身份',
    room_id=30974597,
    openai_api_key=None
)
up.loop()
```
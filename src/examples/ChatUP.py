#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/26 15:03
# @Author  : 雷雨
# @File    : ChatUP.py
# @Desc    :
from langup import ChatUP, Event


# bilibili cookie 通过浏览器edge提取，apikey从.env读取
ChatUP(
    system='你是一位聊天AI助手',
    event_name_list=[Event.TEXT],
    # credential 参数说明
    # 方式一: credential为空，从工作目录/.env文件读取credential
    # 方式二: 直接传入 https://nemo2011.github.io/bilibili-api/#/get-credential
    # credential={"sessdata": 'xxx', "buvid3": 'xxx', "bili_jct": 'xxx'}
    # 方式三: 自动从浏览器资源读取
    # browser='load'
).loop()
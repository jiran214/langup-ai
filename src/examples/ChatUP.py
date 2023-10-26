#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/26 15:03
# @Author  : 雷雨
# @File    : ChatUP.py
# @Desc    :
from langup import ChatUP, Event


# bilibili cookie 通过浏览器edge提取，apikey从.env读取
ChatUP(system='你是一位聊天AI助手', event_name_list=[Event.TEXT], browser='edge').loop()
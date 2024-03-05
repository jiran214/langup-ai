#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

from langup import ChatUP, set_logger

# 需要配置Bilibili、OpenAI
# ...

set_logger()
ChatUP(system='你是一位聊天AI助手').run()
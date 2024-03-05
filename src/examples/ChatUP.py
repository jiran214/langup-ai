#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

from langup import ChatUP

# 需要配置Bilibili、OpenAI
# ...

logging.addLevelName("")
ChatUP(system='你是一位聊天AI助手').run()
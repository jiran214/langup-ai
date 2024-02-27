#!/usr/bin/env python
# -*- coding: utf-8 -*-
from langup import UserInputReplyUP

# 需要配置OpenAI
# ...

# 语音实时识别回复
# 语音识别参数见config.convert
UserInputReplyUP(system='你是一位AI助手', listen='speech').run()
# UserInputReplyUP(system='你是一位AI助手', listen='console').run()
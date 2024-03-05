#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
from urllib.request import getproxies

from langup import UserInputReplyUP, config, set_logger


# 语音实时识别回复
# 语音识别参数见config.convert

set_logger()
# UserInputReplyUP(system='你是一位AI助手', listen='speech').run()
UserInputReplyUP(system='你是一位AI助手', listen='console').run()
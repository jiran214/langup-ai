#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import time

from bilibili_api.session import get_at

from langup import config, VideoCommentUP, set_logger

# config.set_bilibili_config(sessdata='xxx', buvid3='xxx', bili_jct='xxx', dedeuserid='xxx', ac_time_value='xxx')
set_logger()
VideoCommentUP(signals=['锐评一下', '来看看', '评论一下']).run()
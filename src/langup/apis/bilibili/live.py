#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import enum

import httpx
from bilibili_api import live

import langup.utils.utils
from langup import config


async def on_danmaku(event_dict):
    input_vars = {
        'text': event_dict['data']['info'][1],
        'user_name': event_dict['data']['info'][2][1],
        'time': event_dict['data']['info'][9]['ts'],
        'type': LiveInputType.danmu
    }
    return input_vars


async def on_gift(event_dict):
    info = event_dict['data']['data']
    input_vars = {
        'user_name': info['uname'],
        'face': info['face'],
        'action': info['action'],
        'giftName': info['giftName'],
        'time': info['timestamp'],
        'type': LiveInputType.gift
    }
    input_vars['text'] = f"{input_vars['user_name']}{input_vars['action']}了{input_vars['giftName']}"
    return input_vars


async def on_super_chat(event_dict):
    info = event_dict['data']['data']
    user_info = info['user_info']
    input_vars = {
        'user_name': user_info['uname'],
        'face': user_info['face'],
        'text': info['message'],
        'price': info['price'],
        'time': info['start_time'],
        'type': LiveInputType.sc
    }
    return input_vars


def event_wrap(func, mq):
    async def wrap(*args, **kwargs):
        input_vars = await func(*args, **kwargs)
        mq.send(input_vars)
    return wrap


class BlLiveRoom:
    def __init__(self, room_id, mq: langup.utils.utils.MQ):
        self.room = live.LiveDanmaku(
            room_display_id=int(room_id),
            # debug=config.debug,
            credential=config.auth.credential
        )
        self.mq = mq
        self.add_event_listeners()

    def add_event_listeners(self):
        listener_map = {
            'DANMU_MSG': event_wrap(on_danmaku, self.mq),
            'SEND_GIFT': event_wrap(on_gift, self.mq),
            'SUPER_CHAT_MESSAGE': event_wrap(on_super_chat, self.mq),
        }
        for item in listener_map.items():
            self.room.add_event_listener(*item)

    def connect(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.room.connect())
        except httpx.ConnectError:
            raise httpx.ConnectError('如果你开启代理遇到此异常，请导入并设置config.proxy = <your proxy>尝试解决该问题！')


class LiveInputType(enum.Enum):
    danmu = '弹幕'
    gift = '礼物'
    sc = 'sc'
    scheduler = '调度任务'
    user = 'user'

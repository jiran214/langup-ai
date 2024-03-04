#!/usr/bin/env python
# -*- coding: utf-8 -*-
import enum
from typing import TypedDict, Literal, Any, Optional, Union

from langchain.chains.base import Chain
from pydantic import BaseModel, Field, ValidationError

from langup.utils.utils import func


class SessionSchema(TypedDict):
    user_nickname: str
    source_content: str
    uri: str
    source_id: int
    bvid: str
    aid: int
    at_time: int


class EventName(enum.Enum):
    """事件类型:
    + TEXT:           纯文字消息
    + PICTURE:        图片消息
    + WITHDRAW:       撤回消息
    + GROUPS_PICTURE: 应援团图片，但似乎不常触发，一般使用 PICTURE 即可
    + SHARE_VIDEO:    分享视频
    + NOTICE:         系统通知
    + PUSHED_VIDEO:   UP主推送的视频
    + WELCOME:        新成员加入应援团欢迎
    """
    TEXT = "1"
    PICTURE = "2"
    WITHDRAW = "5"
    GROUPS_PICTURE = "6"
    SHARE_VIDEO = "7"
    NOTICE = "10"
    PUSHED_VIDEO = "11"
    WELCOME = "306"


class ChatEvent(TypedDict):
    # content: Union[str, int, Picture, Video]
    content: str
    sender_uid: int
    uid: int


class LiveInputType(enum.Enum):
    # gpt生成
    gift = '礼物'
    user = '普通'
    # 不走gpt
    danmu = '弹幕'
    direct = '直接回复'


class SchedulingEvent(BaseModel):
    live_type: LiveInputType = Field(description='模拟输入类型')
    live_input: str
    time: Optional[str] = Field(description='设定时间，自动解析', examples=['5s', '1m', '1h', '3:11'])
    trigger: Optional[Literal['cron', 'interval']] = None
    trigger_kwargs: dict = {}

    def model_post_init(self, __context: Any) -> None:
        if not (self.time or (self.trigger and self.trigger_kwargs)):
            raise ValidationError('参数time和参数(trigger， trigger_kwargs) 未传入一个')
        if self.time:
            self.time = self.time.lower()
            if ':' in self.time:
                self.trigger = 'cron'
                hours, minutes = self.time.split(':')
                self.trigger_kwargs = {'hours': int(hours), 'minutes': int(minutes)}
            else:
                self.trigger = 'interval'
                if 's' in self.time:
                    self.trigger_kwargs['second'] = int(self.time.replace('s', ''))
                if 'h' in self.time:
                    self.trigger_kwargs['hour'] = int(self.time.replace('h', ''))
                if 'm' in self.time:
                    self.trigger_kwargs['minute'] = int(self.time.replace('m', ''))
                else:
                    raise ValidationError('间隔任务以s h m 结尾')

    def get_scheduler_inputs(self):
        return {'job': func({'type': self.live_type, 'text': self.live_input}), 'trigger': self.trigger,
                **self.trigger_kwargs}


class KeywordReply(BaseModel):
    keyword: str
    content: Union[str, Chain]

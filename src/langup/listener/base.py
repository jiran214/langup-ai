#!/usr/bin/env python
# -*- coding: utf-8 -*-
import abc

from pydantic import BaseModel


class Listener(BaseModel, abc.ABC):
    """监听api 通知绑定消息队列"""

    @abc.abstractmethod
    async def alisten(self):
        return

    class Config:
        arbitrary_types_allowed = True

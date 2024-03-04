#!/usr/bin/env python
# -*- coding: utf-8 -*-
import threading
from typing import Any, Callable, Literal

from apscheduler.events import EVENT_JOB_EXECUTED
from apscheduler.schedulers.background import BackgroundScheduler
from pydantic import Field, BaseModel

from langup.core import Listener
from langup.utils.utils import SimpleMQ


class SchedulerWrapper(Listener):
    mq: SimpleMQ = Field(default_factory=SimpleMQ)
    scheduler: BackgroundScheduler = Field(default_factory=BackgroundScheduler)

    def model_post_init(self, __context: Any) -> None:
        # 添加回调，将job结果暂存到mq
        self._scheduler.add_listener(lambda e: self.mq.put(e.retval), EVENT_JOB_EXECUTED)

    def run(self):
        self._scheduler.start()

    async def alisten(self):
        return self.mq.recv()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
import threading
from typing import Any, Callable, Literal, Iterable
from pydantic import PrivateAttr

from apscheduler.events import EVENT_JOB_EXECUTED
from apscheduler.schedulers.background import BackgroundScheduler
from pydantic import Field

from langup.listener.base import AsyncListener
from langup.listener.schema import SchedulingEvent
from langup.utils.utils import SimpleMQ


class SchedulerWrapper(AsyncListener):
    mq: SimpleMQ = Field(default_factory=SimpleMQ)
    events: Iterable[SchedulingEvent]
    _scheduler: BackgroundScheduler = PrivateAttr(default_factory=BackgroundScheduler)

    def model_post_init(self, __context: Any) -> None:
        # 添加回调，将job结果暂存到mq
        for e in self.events:
            self._scheduler.add_job(**e.get_scheduler_inputs())
        self._scheduler.add_listener(lambda e: self.mq.put(e.retval), EVENT_JOB_EXECUTED)
        self._scheduler.start()

    async def alisten(self):
        return self.mq.recv()

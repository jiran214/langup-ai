import threading
from typing import Callable, Literal, Any

from apscheduler.schedulers.blocking import BlockingScheduler
from pydantic import Field

from langup import base


SchedulerMaster = BlockingScheduler()
lock = threading.Lock()
is_start = False


class JobScheduler(base.Listener):
    scheduler_mq: base.MQ = Field(default_factory=base.SimpleMQ)
    trigger: Literal['date', 'interval', 'cron']
    sche_kwargs: dict
    callback: Callable = Field(description='Callback输出会给到up')
    Schema: Any = None

    def init(self, mq, listener_sleep=None):
        SchedulerMaster.add_job(func=self.scheduler_callback, trigger=self.trigger, **self.sche_kwargs)
        with lock:
            global is_start
            if is_start is False:
                SchedulerMaster.start()
            is_start = True
        super().init(mq, listener_sleep)

    def scheduler_callback(self):
        self.scheduler_mq.send(self.callback())

    async def _alisten(self):
        return self.scheduler_mq.recv()

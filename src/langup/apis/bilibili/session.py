import logging

from bilibili_api import Credential, sync, Picture
from bilibili_api.session import Session, Event, get_at, send_msg

from langup.utils.utils import async_wrapper, MQ


class ChatSession(Session):

    def __init__(self, credential: Credential, mq: MQ):
        self.mq = mq
        super().__init__(credential)
        self.logger.setLevel(level=logging.WARNING)

    def register_handlers(self, event_name_list):
        for event_name in event_name_list:
            self.add_event_listener(event_name, async_wrapper(self.handle))

    async def handle(self, event: Event):
        self.mq.send(event)

    def connect(self):
        sync(self.start())
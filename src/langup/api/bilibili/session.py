from bilibili_api import Credential, sync, Picture
from bilibili_api.session import Session, Event, get_at


from langup.base import MQ
from langup.utils.utils import async_wrapper


class ChatSession(Session):

    def __init__(self, credential: Credential, mq: MQ):
        self.mq = mq
        super().__init__(credential)

    def register_handlers(self, event_name_list):
        for event_name in event_name_list:
            self.add_event_listener(event_name, async_wrapper(self.handle))

    async def handle(self, event: Event):
        self.mq.send(event)

    def connect(self):
        sync(self.start())
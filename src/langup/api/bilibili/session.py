from bilibili_api import Credential, sync, Picture
from bilibili_api.session import Session, Event, get_at


from langup.base import MQ


class ChatSession(Session):

    def __init__(self, credential: Credential, mq: MQ):
        self.mq = mq
        super().__init__(credential)

    def register_handlers(self, event_name_list):
        for event_name in event_name_list:
            self.add_event_listener(event_name)

    async def handle(self, event: Event):
        self.mq.send(event)

    def connect(self):
        sync(self.start())


@session.on(Event.PICTURE)
async def pic(event: Event):
    img: Picture = event.content
    img.download("./")


@session.on(Event.TEXT)
async def reply(event: Event):
    if event.content == "/close":
        session.close()
    elif event.content == "来张涩图":
        img = await Picture.from_file("test.png").upload_file(session.credential)
        await session.reply(event, img)
    else:
        await session.reply(event, "你好李鑫")

sync(session.start())
from pydantic import BaseModel

from langup import api, base, config
from langup.utils import vid_transform
from langup.utils.thread import start_thread


class SessionAtListener(base.Listener):
    class Schema(BaseModel):
        user_nickname: str
        source_content: str
        uri: str
        source_id: str
        bvid: str
        aid: int

    async def _alisten(self):
        sessions = await api.bilibili.session.get_at(config.credential)
        user_nickname = sessions['items'][0]['user']['nickname']
        source_content = sessions['items'][0]['item']['source_content']
        uri = sessions['items'][0]['item']['uri']
        source_id = sessions['items'][0]['item']['source_id']
        bvid = "BV" + uri.split("BV")[1]
        aid = vid_transform.note_query_2_aid(uri)
        return self.Schema(**locals())


class LiveListener(base.Listener):
    Schema: dict = {}
    room_id = None
    max_size = 20

    def __init__(self, mq_list):
        assert self.room_id, 'setattr LiveListener.room_id'
        super().__init__(mq_list)
        self.live_mq = base.SimpleMQ(maxsize=self.max_size)
        self.room = api.bilibili.live.BlLiveRoom(self.room_id, self.live_mq)
        t = start_thread(self.room.connect)

    async def _alisten(self) -> dict:
        return self.live_mq.recv()


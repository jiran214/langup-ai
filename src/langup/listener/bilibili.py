from pydantic import BaseModel

from langup import api, base, config
from langup.utils import vid_transform
from langup.utils.thread import start_thread


class SessionAtListener(base.Listener):
    SLEEP = 60 * 2
    newest_at_time: int = 0

    class Schema(BaseModel):
        user_nickname: str
        source_content: str
        uri: str
        source_id: int
        bvid: str
        aid: int
        at_time: int

    async def _alisten(self):
        sessions = await api.bilibili.session.get_at(config.credential)
        items = sessions['items']
        for item in items[::-1]:
            at_type = item['item']['type']
            if at_type != 'reply':
                continue
            at_time = item['at_time']
            if at_time <= self.newest_at_time:
                continue
            user_nickname = item['user']['nickname']
            source_content = item['item']['source_content']
            uri = item['item']['uri']
            source_id = item['item']['source_id']
            bvid = "BV" + uri.split("BV")[1]
            aid = vid_transform.note_query_2_aid(uri)
            self.newest_at_time = at_time
            return self.Schema(
                user_nickname=user_nickname,
                source_content=source_content,
                uri=uri,
                source_id=source_id,
                bvid=bvid,
                aid=aid,
                at_time=at_time,
            )


class LiveListener(base.Listener):
    Schema: dict = {}
    room_id = None
    max_size = 20

    def __init__(self, mq_list):
        assert self.room_id, 'setattr LiveListener.room_id'
        super().__init__(mq_list)
        self.live_mq = base.SimpleMQ(maxsize=self.max_size)
        self.room = api.bilibili.live.BlLiveRoom(self.room_id, self.live_mq, config.credential)
        t = start_thread(self.room.connect)

    async def _alisten(self) -> dict:
        return self.live_mq.recv()


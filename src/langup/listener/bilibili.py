import enum
from typing import Optional, Type, List, Union

from bilibili_api import Picture
from bilibili_api.session import Event
from pydantic import BaseModel

from langup import api, base, config
from langup.api.bilibili.video import Video
from langup.base import MQ
from langup.utils import vid_transform
from langup.utils.utils import start_thread


class SessionSchema(BaseModel):
    user_nickname: str
    source_content: str
    uri: str
    source_id: int
    bvid: str
    aid: int
    at_time: int


class SessionAtListener(base.Listener):
    listener_sleep: int = 60 * 2
    newest_at_time: int = 0
    Schema: Type[SessionSchema] = SessionSchema

    async def _alisten(self):
        sessions = await api.bilibili.session.get_at(config.credential)
        items = sessions['items']
        schema_list = []
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
            schema_list.append(self.Schema(
                user_nickname=user_nickname,
                source_content=source_content,
                uri=uri,
                source_id=source_id,
                bvid=bvid,
                aid=aid,
                at_time=at_time,
            ))
        return schema_list


class LiveListener(base.Listener):
    room_id: int
    max_size: int = 20
    Schema: dict = {}  # text type ...
    live_mq: Optional[MQ] = None

    def init(self, mq, listener_sleep=None):
        self.live_mq = base.SimpleMQ(maxsize=self.max_size)
        room = api.bilibili.live.BlLiveRoom(self.room_id, self.live_mq, config.credential)
        t = start_thread(room.connect)
        super().init(mq, listener_sleep)

    async def _alisten(self) -> dict:
        return self.live_mq.recv()


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


class ChatEvent(BaseModel):
    # content: Union[str, int, Picture, Video]
    content: str
    sender_uid: int
    uid: int


class ChatListener(base.Listener):
    event_name_list: List[EventName]

    Schema: Type[Event] = ChatEvent
    listener_sleep: int = 6
    max_size: Optional[int] = 0
    session_mq: Optional[MQ] = None

    def init(self, mq: MQ, listener_sleep: Optional[int] = 0):
        self.session_mq = base.SimpleMQ(maxsize=self.max_size)
        s = api.bilibili.session.ChatSession(credential=config.credential, mq=self.session_mq)
        s.register_handlers([event_name.value for event_name in self.event_name_list])
        t = start_thread(s.connect)
        super().init(mq, listener_sleep)

    async def _alisten(self):
        event: Event = self.session_mq.recv()
        return ChatEvent(
            sender_uid=event.sender_uid,
            uid=event.uid,
            content=event.content
        )

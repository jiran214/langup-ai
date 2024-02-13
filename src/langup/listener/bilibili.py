import enum
from typing import Optional, Type, List, Union, ClassVar, Any, TypedDict
from bilibili_api.session import Event
from bilibili_api import bvid2aid

from pydantic import BaseModel

import langup.core
import langup.utils.utils
from langup import apis, config
from langup.utils.utils import start_thread, MQ


def note_query_2_aid(note_query: str):
    if note_query.startswith('BV'):
        aid = bvid2aid(note_query)
    elif note_query.startswith('https://www.bilibili.com/video/BV'):
        bv = note_query.split('https://www.bilibili.com/video/')[1].split('/')[0]
        aid = bvid2aid(bv)
    else:
        aid = note_query

    return int(aid)


class SessionSchema(TypedDict):
    user_nickname: str
    source_content: str
    uri: str
    source_id: int
    bvid: str
    aid: int
    at_time: int


class SessionAtListener(langup.core.Listener):
    newest_at_time: int = 0
    aid_record_map: set = set()

    def check_config(self):
        config.auth.check_bilibili_config()

    async def alisten(self) -> Optional[SessionSchema]:
        sessions = await apis.bilibili.session.get_at(config.auth.credential)
        items = sessions['items']
        if not items:
            return
        schema_list = []
        item = items[-1]
        at_type = item['item']['type']
        if at_type != 'reply':
            return
        at_time = item['at_time']
        if at_time <= self.newest_at_time:
            return
        user_nickname = item['user']['nickname']
        source_content = item['item']['source_content']
        uri = item['item']['uri']
        source_id = item['item']['source_id']
        bvid = "BV" + uri.split("BV")[1]
        aid = note_query_2_aid(uri)
        if aid in self.aid_record_map:
            return
        self.newest_at_time = at_time
        schema = dict(
            user_nickname=user_nickname,
            source_content=source_content,
            uri=uri,
            source_id=source_id,
            bvid=bvid,
            aid=aid,
            at_time=at_time,
        )
        self.aid_record_map.add(schema['aid'])
        return schema


class LiveListener(langup.core.Listener):
    room_id: int
    max_size: int = 20
    live_mq: Optional[MQ] = None

    def model_post_init(self, __context: Any) -> None:
        config.auth.check_bilibili_config()
        self.live_mq = langup.utils.utils.SimpleMQ(maxsize=self.max_size)
        room = apis.bilibili.live.BlLiveRoom(self.room_id, self.live_mq)
        t = start_thread(room.connect)

    async def alisten(self) -> dict:
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


class ChatEvent(TypedDict):
    # content: Union[str, int, Picture, Video]
    content: str
    sender_uid: int
    uid: int


class ChatListener(langup.core.Listener):
    event_name_list: List[EventName]
    max_size: Optional[int] = 0
    session_mq: Optional[MQ] = None

    def model_post_init(self, __context: Any) -> None:
        config.auth.check_bilibili_config()
        self.session_mq = langup.utils.utils.SimpleMQ(maxsize=self.max_size)
        s = apis.bilibili.session.ChatSession(credential=config.auth.credential, mq=self.session_mq)
        s.register_handlers([event_name.value for event_name in self.event_name_list])
        t = start_thread(s.connect)

    async def alisten(self) -> ChatEvent:
        event: Event = self.session_mq.recv()
        return dict(sender_uid=event.sender_uid, uid=event.uid, content=event.content)

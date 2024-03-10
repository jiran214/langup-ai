import logging
import time
from typing import Optional, List, Any, Iterable, AsyncGenerator
from bilibili_api.session import Event, Session, EventType, get_at
from bilibili_api import bvid2aid

from langup import apis, config
from langup.listener.base import AsyncListener
from langup.listener.schema import SessionSchema, EventName
from langup.utils.utils import start_thread, SimpleMQ

logger = logging.getLogger('langup.listener')


def note_query_2_aid(note_query: str):
    if note_query.startswith('BV'):
        aid = bvid2aid(note_query)
    elif note_query.startswith('https://www.bilibili.com/video/BV'):
        bv = note_query.split('https://www.bilibili.com/video/')[1].split('/')[0]
        aid = bvid2aid(bv)
    else:
        aid = note_query

    return int(aid)


async def SessionAtGenerator(
    signals: Iterable[str],
    newest_at_time: int = int(time.time())
) -> AsyncGenerator[Any, Optional[SessionSchema]]:
    aid_record_map = set()
    while 1:
        sessions = await get_at(config.credential)
        items = sessions['items']
        if not items:
            yield
        for item in items:
            user_nickname = item['user']['nickname']
            source_content = item['item']['source_content']
            if not any([
                signal in source_content for signal in signals
            ]):
                logger.info(f"过滤,没有出现暗号:{source_content}")
                continue
            at_time = item['at_time']
            logger.debug(f"最新消息:{at_time=} {user_nickname=} {source_content=}")
            at_type = item['item']['type']
            if at_type != 'reply':
                continue
            # 最新的消息在最前面
            if at_time <= newest_at_time:
                break
            uri = item['item']['uri']
            source_id = item['item']['source_id']
            bvid = "BV" + uri.split("BV")[1]
            aid = note_query_2_aid(uri)
            if aid in aid_record_map:
                break
            newest_at_time = at_time
            schema = dict(
                user_nickname=user_nickname,
                source_content=source_content,
                uri=uri,
                source_id=source_id,
                bvid=bvid,
                aid=aid,
                at_time=at_time,
            )
            aid_record_map.add(schema['aid'])
            yield schema
        yield


class LiveListener(AsyncListener):
    room_id: int
    max_size: int = 20
    live_mq: Optional[SimpleMQ] = None

    def model_post_init(self, __context: Any) -> None:
        self.live_mq = SimpleMQ(maxsize=self.max_size)
        room = apis.bilibili.live.BlLiveRoom(self.room_id, self.live_mq)
        logger.info(f'开启线程:LiveListener')
        t = start_thread(room.connect)

    async def alisten(self) -> dict:
        """dict key: text username..."""
        return self.live_mq.recv()


class ChatListener(AsyncListener):
    event_name_list: List[EventName] = [EventName.TEXT]
    max_size: Optional[int] = 0
    session_mq: Optional[SimpleMQ] = None

    def model_post_init(self, __context: Any) -> None:
        self.session_mq = SimpleMQ(maxsize=self.max_size)
        session = Session(config.credential)

        @session.on(EventType.TEXT)
        async def reply(event: Event):
            self.session_mq.send(event)
        logger.info(f'开启线程: ChatListener')
        start_thread(session.start)

    async def alisten(self) -> dict:
        """dict key: content sender_uid uid"""
        event: Event = self.session_mq.recv()
        return dict(sender_uid=event.sender_uid, uid=event.uid, text=event.content)

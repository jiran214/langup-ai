from typing import Union

from bilibili_api import Credential, Picture
from bilibili_api.session import send_msg, Event

from langup import base, config
from langup.api.bilibili import comment


class CommentReaction(base.Reaction):

    aid: int
    content: str

    async def areact(self):
        # 发送评论
        await comment.send_comment(text=self.content, type_=comment.CommentResourceType.VIDEO, oid=self.aid, credential=config.credential)


class ChatReaction(base.Reaction):
    uid: int
    sender_uid: int
    # content: Union[str, Picture]
    content: str

    async def areact(self):
        if self.uid == self.sender_uid:
            self.logger.error("不能给自己发送消息哦~")
        else:
            msg_type = Event.PICTURE if isinstance(self.content, Picture) else Event.TEXT
            return await send_msg(config.credential, self.sender_uid, msg_type, self.content)

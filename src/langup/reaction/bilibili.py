from langup import base, config
from langup.api.bilibili import comment


class CommentReaction(base.Reaction):

    aid: int
    content: str

    async def areact(self):
        # 发送评论
        await comment.send_comment(text=self.content, type_=comment.CommentResourceType.VIDEO, oid=self.aid, credential=config.credential)


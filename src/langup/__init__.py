from langup.utils.utils import get_cookies, set_langchain_debug, set_logger

try:
    from langchain.chains.base import Chain
except:
    # python版本和pydantic不兼容问题
    from pydantic.v1 import typing
    typing.evaluate_forwardref = lambda type_, globalns, localns: type_._evaluate(globalns, localns)


from langup import config
from langup.uploader.simple import UserInputReplyUP
from langup.uploader.bilibili import VideoCommentUP, VtuBer, ChatUP, DynamicUP

__all__ = [
    'get_cookies',
    'set_langchain_debug',
    'set_logger',

    'config',
    'DynamicUP',
    'VideoCommentUP',
    'UserInputReplyUP',
    'VtuBer',
    'ChatUP',
]


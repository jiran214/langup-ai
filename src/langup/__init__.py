from typing import Union, Callable


from langup.config import VERSION

try:
    from langchain.chains.base import Chain
    BrainType = Union[Chain, Callable]
except:
    # python版本和pydantic不兼容问题
    from pydantic.v1 import typing
    typing.evaluate_forwardref = lambda type_, globalns, localns: type_._evaluate(globalns, localns)


from langup import config
from langup.uploader.simple import UserInputReplyUP
from langup.uploader.bilibili import VtuBer, VideoCommentUP, ChatUP
from bilibili_api import Credential
from bilibili_api.session import Event


__version__ = VERSION


__all__ = [
    'Credential',
    'config',
    'BrainType',
    'Event',
    'base',

    'VideoCommentUP',
    'UserInputReplyUP',
    'VtuBer',
    'ChatUP',
]


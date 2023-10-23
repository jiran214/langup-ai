from typing import Union, Callable


try:
    from langchain.chains.base import Chain
    BrainType = Union[Chain, Callable]
except:
    # python版本和pydantic不兼容问题
    from pydantic.v1 import typing
    typing.evaluate_forwardref = lambda type_, globalns, localns: type_._evaluate(globalns, localns)


from langup import config
from langup.uploader.simple import UserInputReplyUP
from langup.uploader.bilibili import VtuBer, VideoCommentUP
from bilibili_api import Credential

__all__ = [
    'Credential',
    'config',
    'BrainType',
    'base',

    'VideoCommentUP',
    'UserInputReplyUP',
    'VtuBer',
]


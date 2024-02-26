try:
    from langchain.chains.base import Chain
except:
    # python版本和pydantic不兼容问题
    from pydantic.v1 import typing
    typing.evaluate_forwardref = lambda type_, globalns, localns: type_._evaluate(globalns, localns)


from langup.chains import LLMChain
from langup.config import VERSION
from langup.core import Langup, RunManager
from langup import config
from langup.uploader.simple import UserInputReplyUP
from langup.uploader.bilibili import VideoCommentUP, VtuBer, ChatUP
from langup.listener.schema import EventName
from bilibili_api import Credential


__version__ = VERSION


__all__ = [
    'Credential',
    'config',
    'LLMChain',
    'Langup',
    'RunManager',

    'VideoCommentUP',
    'UserInputReplyUP',
    'VtuBer',
    'ChatUP',
]


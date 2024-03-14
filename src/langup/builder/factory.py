#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Iterable

from langup.builder.base import Flow, ContextBuilder, LLMBuilder, ReactBuilder
from langup.builder.simple import ChatModelBuilder


def get_flow(base_class=Flow, builders: Iterable = tuple()):
    _classes = []
    for _class in builders:
        expected = issubclass(_class, (ContextBuilder, LLMBuilder, ReactBuilder))
        assert expected, 'plugin 不属于(contextBuilder, LLMBuilder, ReactBuilder)'
        _classes.append(_class)
    _classes.append(base_class)
    return type('ChainBuilder', tuple(_classes), {})


def get_chat_flow(builders: Iterable = tuple()):
    builders = list(builders)
    builders.append(ChatModelBuilder)
    return get_flow(builders=builders)


class ChatFlow(Flow, ChatModelBuilder):
    pass
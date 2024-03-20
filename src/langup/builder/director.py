#!/usr/bin/env python
# -*- coding: utf-8 -*-
from operator import itemgetter
from typing import Iterable

from langchain_core.runnables import Runnable, RunnableAssign, RunnablePassthrough, chain
from pydantic import Field

from langup.builder.base import ContextBuilder, LLMBuilder, ReactBuilder
from langup.builder.extends import ChatModelBuilder, KeywordRouteBuilder, ReactFilterBuilder, AgentBuilder, ChatHistoryBuilder


class Flow(ContextBuilder, LLMBuilder, ReactBuilder):

    def get_flow(self) -> Runnable:
        """
        默认flow 感知 -> (上下文 -> 思考 -> 行为)
        Returns:
            langchain Runnable
        """
        return (
            RunnableAssign(**self.context)
            | RunnableAssign(**{self.llm_output_key: self.get_brain()})
            | self.react
        )


class SimpleFlow(Flow, ChatModelBuilder):
    pass


class ReflectFlow(Flow, KeywordRouteBuilder, ReactFilterBuilder, AgentBuilder, ChatHistoryBuilder):

    def get_brain(self):
        @chain
        def route():
            if reflect := self.get_reflect():
                return reflect
            return super().get_brain()
        return route

    def get_flow(self) -> Runnable:
        """
        flow 感知 -> (上下文 -> 回忆 -> 反射/思考 -> 过滤 -> 行为)
        Returns:
            langchain Runnable
        """

        if self._redis_client:
            self.context['history'] = itemgetter(self._input_messages_key) | chain(self.load_history)
            self.react = chain(self.save_history) | self.react

        if _filter := self.get_filter():
            self.react = _filter | self.react

        _chain = (
            RunnableAssign(**self.context)
            | RunnableAssign(**{self.llm_output_key: self.get_brain()})
            | self.react
        )
        return _chain
#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Iterable

from langchain_core.runnables import Runnable, RunnableAssign, RunnablePassthrough, chain
from pydantic import Field

from langup.builder.base import ContextBuilder, LLMBuilder, ReactBuilder
from langup.builder.extends import ChatModelBuilder, KeywordRouteBuilder, ReactFilterBuilder, AgentBuilder


class Flow(ContextBuilder, LLMBuilder, ReactBuilder):
    """编排节点"""
    llm_output_key: str = Field('output', description='llm输出key名称')

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


class ChatFlow(Flow, KeywordRouteBuilder, ReactFilterBuilder, AgentBuilder):

    def get_flow(self) -> Runnable:
        """
        flow 感知 -> (上下文 -> 反射/思考 -> 过滤 ->行为)
        Returns:
            langchain Runnable
        """
        @chain
        def route():
            if self._keyword_chain and (keyword_res := self._keyword_chain):
                return keyword_res
            return self.get_brain()

        _chain = (
            RunnableAssign(**self.context)
            | RunnableAssign(**{self.llm_output_key: route})
            | self._filter_chain
            | self.react
        )
        return _chain
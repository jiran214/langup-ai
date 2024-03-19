#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from typing import Optional, Sequence

from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain_core.language_models import BaseChatModel, BaseLanguageModel
from langchain_core.runnables import chain, Runnable, RunnablePassthrough
from langchain_core.tools import BaseTool

from langup.builder import base

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from pydantic import model_validator, PrivateAttr

from langup.listener.schema import KeywordReply
from langup.utils.utils import KeywordsMatcher, BanWordsFilter, Continue


logger = logging.getLogger('langup.extends')


class ChatModelBuilder(base.LLMBuilder):
    system: Optional[str] = None
    human: str = '{input}'

    def set_chat_model(self, model: BaseChatModel):
        self.llm = model

    def set_chatgpt(
            self,
            openai_api_key=None,
            openai_api_base=None,
            model_name="gpt-3.5-turbo",
            openai_proxy=None,
            max_retries=1,
            request_timeout=60,
            **openai_kwargs
    ):
        openai_kwargs.update(openai_api_key=openai_api_key, openai_api_base=openai_api_base, model_name=model_name,
                             openai_proxy=openai_proxy, max_retries=max_retries, request_timeout=request_timeout)
        self.llm = ChatOpenAI(**openai_kwargs)

    @model_validator(mode='after')
    def __set_prompt(self):
        if self.system:
            self.prompt = ChatPromptTemplate.from_messages([
                ('system', self.system),
                ('human', self.human)
            ])
        return self


class AgentBuilder(base.LLMBuilder):
    def set_agent(self, tools: Sequence[BaseTool], verbose=True):
        assert isinstance(self.llm, BaseLanguageModel), 'Please set llm first'
        assert not self.chain, 'chain already pass'
        assert isinstance(self.prompt, ChatPromptTemplate)
        agent = create_openai_functions_agent(self.llm, tools, self.prompt)
        # Create an agent executor by passing in the agent and tools
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=verbose)
        self.chain = agent_executor


class KeywordRouteBuilder(base.LLMBuilder):
    _keywords_matcher: Optional[KeywordsMatcher] = PrivateAttr()
    _keyword_chain: Runnable = PrivateAttr()
    _match_input_key: str = '__all__'

    def match(self, _dict):
        match_data = str(_dict) if self._match_input_key == '__all__' else _dict.get(self._match_input_key, '')
        if self.keywords_matcher and (callback := self.keywords_matcher.match(match_data)):
            return callback

    def set_keywords_matcher(self, keyword_replies: Sequence[KeywordReply], match_input_key='__all__'):
        self._match_input_key = match_input_key
        self._keywords_matcher = KeywordsMatcher({reply.keyword: reply.content for reply in keyword_replies})
        self._keyword_chain = chain(self.match)


class ReactFilterBuilder(base.ReactBuilder):
    _ban_word_filter: Optional[BanWordsFilter] = PrivateAttr()
    _filter_chain: Runnable = RunnablePassthrough()
    _filter_key: str = '__all__'

    def filter(self, _dict):
        _value = str(_dict) if self._match_input_key == '__all__' else _dict.get(self._filter_key, '')
        if kws := self.ban_word_filter.match(_dict):
            raise Continue(f'包含违禁词:{_dict=} {kws=}')
        return _dict

    def set_ban_words(self, extra_ban_words: Sequence[str] = tuple(), filter_key='__all__'):
        self._filter_key = filter_key
        self._ban_word_filter = BanWordsFilter(extra_ban_words=extra_ban_words)
        self._filter_chain = chain(self.filter)
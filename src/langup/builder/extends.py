#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
from operator import itemgetter
from typing import Optional, Sequence, TYPE_CHECKING

from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain_community.chat_message_histories import RedisChatMessageHistory, ChatMessageHistory
from langchain_community.utilities.redis import get_client
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.language_models import BaseChatModel, BaseLanguageModel
from langchain_core.messages import messages_from_dict, BaseMessage, message_to_dict, ChatMessage
from langchain_core.runnables import chain, Runnable, RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.tools import BaseTool

from langup.builder import base

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
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


class ChatHistoryBuilder(base.ContextBuilder, ChatModelBuilder, base.ReactBuilder):
    _redis_client: 'RedisType' = PrivateAttr()
    _key_prefix: str = PrivateAttr()
    _ttl: Optional[int] = PrivateAttr(),
    _input_messages_key: str = PrivateAttr()

    @property
    def key(self) -> str:
        """Construct the record key to use"""
        return self._key_prefix + self.session_id

    def load_history(self, _dict) -> List[BaseMessage]:  # type: ignore
        """Retrieve the messages from Redis"""
        assert self._input_messages_key in _dict
        _items = self._redis_client.lrange(f"{self._key_prefix}{_dict[self._input_messages_key]}", 0, -1)
        items = [json.loads(m.decode("utf-8")) for m in _items[::-1]]
        messages = messages_from_dict(items)
        return messages

    def save_history(self, _dict):
        """Append the message to the record in Redis"""
        key = f"{self._key_prefix}{_dict[self._input_messages_key]}"
        self.redis_client.lpush(key, json.dumps(ChatMessage(role='human', content=self.human.format(**_dict))))
        self.redis_client.lpush(key, json.dumps(ChatMessage(role='ai', content=_dict[self.llm_output_key])))
        if self.ttl:
            self._redis_client.expire(key, self._ttl)
        return _dict

    def clear(self, key) -> None:
        """Clear session memory from Redis"""
        self._redis_client.delete(key)

    def set_history(
            self,
            input_messages_key: str,
            url: str = "redis://localhost:6379/0",
            key_prefix: str = "message_store:",
            ttl: Optional[int] = None
    ):
        self.prompt: ChatPromptTemplate
        assert len(self.prompt.messages) == 2, 'prompt length error'
        self._key_prefix = key_prefix
        self._ttl = ttl
        self._input_messages_key = input_messages_key
        self.prompt = ChatPromptTemplate(messages=[
            self.prompt.messages[0], MessagesPlaceholder(variable_name="history"), self.prompt.messages[-1]]
        )
        self._redis_client = get_client(redis_url=url)


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
    _keyword_chain: Runnable = RunnablePassthrough()
    _match_input_key: str = '__all__'

    def match(self, _dict):
        match_data = str(_dict) if self._match_input_key == '__all__' else _dict.get(self._match_input_key, '')
        if self.keywords_matcher and (callback := self.keywords_matcher.match(match_data)):
            return callback

    def set_keywords_matcher(self, keyword_replies: Sequence[KeywordReply], match_input_key='__all__'):
        self._match_input_key = match_input_key
        self._keywords_matcher = KeywordsMatcher({reply.keyword: reply.content for reply in keyword_replies})
        self._keyword_chain = chain(self.match)

    def get_reflect(self):
        return self._keywords_matcher


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

    def get_filter(self):
        return self._filter_chain

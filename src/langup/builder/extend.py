#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Optional, Sequence

from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain_core.language_models import BaseChatModel, BaseLanguageModel
from langchain_core.tools import BaseTool

from langup.builder import base

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from pydantic import model_validator


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
        assert self.llm, 'Please set llm first'
        assert isinstance(self.llm, BaseLanguageModel)
        assert isinstance(self.prompt, ChatPromptTemplate)
        agent = create_openai_functions_agent(self.llm, tools, self.prompt)
        # Create an agent executor by passing in the agent and tools
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=verbose)
        self.chain = agent_executor


class KeywordRouteBuilder(base.LLMBuilder):
    pass


class ReactFilterBuilder(base.ReactBuilder):
    pass
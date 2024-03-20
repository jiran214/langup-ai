#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
from typing import Union, Callable, Iterable, Dict, Optional

from langchain_core.runnables import RunnablePassthrough, Runnable, chain, RunnableParallel
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, model_validator, Field

from langup.utils.utils import has_overridden_method, callable_to_chain

ReactType = Union[Runnable, dict, Callable]


class Builder(BaseModel):
    class Config:
        arbitrary_types_allowed = True


class ContextBuilder(Builder):
    """构造外部知识层节点"""
    context: Dict[str, Union[Runnable, Callable]] = Field(default_factory=RunnablePassthrough, description='外部知识map')

    @model_validator(mode='before')
    def __set_context(self):
        for k in self.react.keys():
            self.context[k] = callable_to_chain(self.react[k])


class LLMBuilder(Builder):
    """构造思考层节点"""
    prompt: Union[Runnable, dict] = Field(default_factory=RunnablePassthrough, description='langchain prompt_temple')
    llm: Runnable = Field(default_factory=RunnablePassthrough, description='langchain llm model')
    parser: Runnable = Field(default_factory=StrOutputParser, description='langchain output_parser')
    chain: Optional[Runnable] = Field(None, description='手动传入chain替代builder原始chain')
    """llm输出key"""
    llm_output_key: str = Field('output', description='llm输出key名称')

    def get_brain(self):
        return self.chain or (self.prompt | self.llm | self.parser)


class ReactBuilder(Builder):
    """构造行为层节点"""
    react: ReactType = Field(default_factory=RunnablePassthrough, description='行为runnable')
    reacts: Iterable[Union[Runnable, Callable]] = Field([], description='行为列表')

    async def _areact(self, _dict): ...
    def _react(self, _dict): ...

    @model_validator(mode='after')
    def __merge_reacts(self):
        """叠加所有的行为
        react直接传入 / 继承重写方法_areact  / 继承重写方法_react / reacts 多行为列表
        """
        _reacts = []
        react_map = {}

        if self.model_fields_set.issuperset({'react'}):
            if isinstance(self.react, dict):
                for k in self.react.keys():
                    react_map[k] = callable_to_chain(self.react[k])
            else:
                _reacts.append(callable_to_chain(self.react))

        if has_overridden_method(self, '_areact'):
            _reacts.append(chain(self._areact))

        if has_overridden_method(self, '_react'):
            _reacts.append(chain(self._react))

        _reacts.extend(self.reacts)
        for _react in _reacts:
            # 重名解决
            if _react.name in react_map:
                _react.name = f'react_{int(time.time())}'
            react_map[_react.name] = _react

        if len(react_map) == 1:
            _, self.react = react_map.popitem()
        else:
            self.react = react_map
        return self



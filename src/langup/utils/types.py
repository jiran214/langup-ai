#!/usr/bin/env python
# -*- coding: utf-8 -*-
import typing
from typing import Callable, Union, Generator, AsyncGenerator, Any

from langchain_core.runnables import Runnable

if typing.TYPE_CHECKING:
    from langup.listener.base import AsyncListener

ReactType = Union[Callable[[Union[str, dict]], Any], Runnable]
ListenerType = Union[Generator, AsyncGenerator, AsyncListener]
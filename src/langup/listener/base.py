#!/usr/bin/env python
# -*- coding: utf-8 -*-
import abc

from pydantic import BaseModel


class AsyncListener(BaseModel, abc.ABC):
    """监听api"""

    @abc.abstractmethod
    async def alisten(self):
        return

    class Config:
        arbitrary_types_allowed = True

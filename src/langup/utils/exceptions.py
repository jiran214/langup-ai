#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/15 15:32
# @Author  : 雷雨
# @File    : exceptions.py
# @Desc    :

class ReactionConstructError(Exception):
    def __init__(self, reaction_kwargs):
        self.reaction_kwargs = reaction_kwargs

    def __str__(self):
        return f"Reaction构造错误参数:{str(self.reaction_kwargs)}"

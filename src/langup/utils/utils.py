#!/usr/bin/env python
# -*- coding: utf-8 -*-]
import abc
import copy
import functools
import queue
import threading
from asyncio import iscoroutinefunction
from http.cookiejar import CookieJar
from typing import Optional, Any, Literal, Callable, List, Union, Iterable
import browser_cookie3
from bilibili_api import sync
from langchain.chains.base import Chain
from langchain_core.runnables import RunnableLambda, Runnable, chain
from pydantic import BaseModel

from langup import config
from langup.utils.consts import color_map, style_map


class Continue(Exception):
    pass


def singleton(cls):
    _instance = {}

    @functools.wraps(cls)
    def inner(*args, **kwargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kwargs)
        return _instance[cls]

    return inner


def format_print(text: str, color: str = 'white', style: str = 'normal', end='\n'):
    color_code = color_map.get(color, "39")
    style_code = style_map.get(style, "0")
    print(f"\033[{style_code};{color_code}m{text}\033[0m", end=end)


def get_cookies(
        domain_name: str,
        browser: Literal[
            'chrome', 'chromium', 'opera', 'opera_gx', 'brave',
            'edge', 'vivaldi', 'firefox', 'librewolf', 'safari', 'load'
        ] = 'load',
        key_lower=True
):
    cookie_dict = {}
    try:
        cj: CookieJar = getattr(browser_cookie3, browser)(domain_name=domain_name)
        for cookie in cj:
            name = cookie.name
            if key_lower:
                name = name.lower()
            cookie_dict[name] = cookie.value
    except PermissionError as e:
        raise PermissionError("""浏览器文件被占用，遇到此错误请尝试: 任务管理器彻底关闭进程""")
    return cookie_dict


def start_thread(job: Callable):
    """启动线程"""
    if iscoroutinefunction(job):
        sync_job = lambda: sync(job())
    else:
        sync_job = job
    t = threading.Thread(target=sync_job)
    t.start()
    return t


class DFA:
    def __init__(self, keyword_list: list):
        self.kw_list = keyword_list
        self.state_event_dict = self._generate_state_event_dict(keyword_list)

    def match(self, content: str):
        if not content:
            return
        match_list = []
        state_list = []
        temp_match_list = []

        for char_pos, char in enumerate(content):
            if char in self.state_event_dict:
                state_list.append(self.state_event_dict)
                temp_match_list.append({
                    "start": char_pos,
                    "match": ""
                })

            for index, state in enumerate(state_list):
                is_find = False
                state_char = None

                # 如果是 * 则匹配所有内容
                if "*" in state:
                    state_list[index] = state["*"]
                    state_char = state["*"]
                    is_find = True

                if char in state:
                    state_list[index] = state[char]
                    state_char = state[char]
                    is_find = True

                if is_find:
                    temp_match_list[index]["match"] += char

                    if state_char["is_end"]:
                        match_list.append(copy.deepcopy(temp_match_list[index]))

                        if len(state_char.keys()) == 1:
                            state_list.pop(index)
                            temp_match_list.pop(index)
                else:
                    state_list.pop(index)
                    temp_match_list.pop(index)

        return match_list

    @staticmethod
    def _generate_state_event_dict(keyword_list: list) -> dict:
        state_event_dict = {}

        for keyword in keyword_list:
            if not keyword:
                continue
            current_dict = state_event_dict
            length = len(keyword)

            for index, char in enumerate(keyword):
                if char not in current_dict:
                    next_dict = {"is_end": False}
                    current_dict[char] = next_dict
                else:
                    next_dict = current_dict[char]
                current_dict = next_dict
                if index == length - 1:
                    current_dict["is_end"] = True

        return state_event_dict


@singleton
class BanWordsFilter(DFA):
    default_path = config.root + '/data/ban_words.txt'

    def __init__(self, file_path_list=None, extra_ban_words: Optional[Iterable[str]] = None):
        file_path_list = (file_path_list or []) + [self.default_path]
        keyword_list = []
        for path in file_path_list:
            keyword_list += [
                line.strip()
                for line in open(file=path, encoding='utf-8', mode='r').readlines()
            ]
        keyword_list.extend((extra_ban_words and list(extra_ban_words)) or [])
        super().__init__(keyword_list)


class KeywordsMatcher(DFA):

    def __init__(self, keyword_map: dict):
        self.keyword_map = keyword_map
        super().__init__(list(keyword_map.keys()))

    def match(self, content: str) -> Union[None, Chain, str]:
        res = super().match(content)
        return res and self.keyword_map.get(res[0]['match'])


class SimpleMQ(queue.Queue):

    def recv(self) -> Union[BaseModel, dict]:
        return self.get()

    def send(self, schema):
        # 设置maxsize淘汰旧消息
        if self.maxsize != 0 and self.qsize() == self.maxsize:
            self.get()
        self.put(schema)


def set_langchain_debug(v: bool = True):
    from langchain.globals import set_debug
    set_debug(v)


def set_logger():
    import logging
    logger = logging.getLogger('langup')
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)
    return logger


def import_module(lib, class_name):
    import importlib
    module = f'{lib}.{class_name}'
    try:
        Module = importlib.import_module(module)
    except ImportError:
        raise ImportError(f"Import {lib}.{class_name} error. Please `pip install {lib}`")
    return Module


def has_overridden_method(instance, method_name):
    method = getattr(instance, method_name)

    for cls in instance.__class__.mro()[1:-1]:
        if method_name in vars(cls):
            return method != getattr(cls, method_name)
    return False


def callable_to_chain(func):
    if isinstance(func, Callable):
        return chain(func)
    elif isinstance(func, Runnable):
        return func
    raise AttributeError(f"{func} 不为Runnable或可调用对象")
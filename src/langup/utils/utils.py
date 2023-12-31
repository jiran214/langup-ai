#!/usr/bin/env python
# -*- coding: utf-8 -*-]
import copy
import functools
import threading
from asyncio import iscoroutinefunction
from http.cookiejar import CookieJar
from typing import Optional, Any, Literal, Callable
import browser_cookie3
from bilibili_api import sync

from pydantic import BaseModel

color_map = {
    "black": "30",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "magenta": "35",
    "cyan": "36",
    "white": "39"
}

style_map = {
    "normal": "0",
    "bold": "1",
    "underline": "4",
    "reverse": "7"
}


def singleton(cls):
    _instance = {}

    @functools.wraps(cls)
    def inner(*args, **kwargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kwargs)
        return _instance[cls]
    return inner


class DFA:
    def __init__(self, keyword_list: list):
        self.kw_list = keyword_list
        self.state_event_dict = self._generate_state_event_dict(keyword_list)

    def match(self, content: str):
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


class Record(BaseModel):
    """存档、日志"""
    listener_kwargs: Optional[Any] = None
    react_kwargs: Optional[dict] = None
    time_cost: Optional[str] = None
    created_time: Optional[str] = None


def format_print(text: str, color: str = 'white', style: str = 'normal', end='\n'):

    color_code = color_map.get(color, "39")
    style_code = style_map.get(style, "0")

    print(f"\033[{style_code};{color_code}m{text}\033[0m", end=end)


def get_list(item):
    if isinstance(item, list):
        return item
    else:
        return [item]


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


def async_wrapper(fun):
    """带参数的协程函数变成coroutine对象"""
    @functools.wraps(fun)
    async def wrap(*args, **kwargs):
        await fun(*args, **kwargs)
    return wrap


def start_thread(job: Callable):
    """启动线程"""
    if iscoroutinefunction(job):
        sync_job = lambda: sync(job())
    else:
        sync_job = job
    t = threading.Thread(target=sync_job)
    t.start()
    return t
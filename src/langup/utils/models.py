#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from urllib.request import getproxies

import httpx
from langchain_openai import ChatOpenAI

from langup import config


def set_openai_model():
    openai_proxy = config.auth.openai_kwargs.get('openai_proxy') or config.proxy or getproxies().get('http') or None
    proxies = openai_proxy and {'http://': openai_proxy, 'https://': openai_proxy}
    chat_model_kwargs = {
        'max_retries': 1,
        'http_client': proxies and httpx.AsyncClient(proxies=proxies),
        'request_timeout': 60,
        **config.auth.openai_kwargs,
    }
    _model = ChatOpenAI(**chat_model_kwargs)
    config.auth.check_openai_config()
    return _model



from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from urllib.request import getproxies

import httpx
from langchain_openai import ChatOpenAI

from langup import config


def Prompt(system: str, human: str = '{input}'):
    return ChatPromptTemplate.from_messages([
        ('system', system),
        ('human', human)
    ])


def LLM(
    openai_api_key=None,
    openai_proxy=None,
    openai_api_base=None,
    model_name="gpt-3.5-turbo",
    **openai_kwargs
):
    openai_proxy = openai_proxy or config.proxy or getproxies().get('http') or None
    proxies = openai_proxy and {'http://': openai_proxy, 'https://': openai_proxy}
    openai_kwargs.update(openai_api_key=openai_api_key, openai_api_base=openai_api_base, model_name=model_name)
    chat_model_kwargs = {
        'max_retries': 1,
        'http_client': proxies and httpx.AsyncClient(proxies=proxies),
        'request_timeout': 60,
        **openai_kwargs,
    }
    _model = ChatOpenAI(**chat_model_kwargs) | StrOutputParser()
    return _model


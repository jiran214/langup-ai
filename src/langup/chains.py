from typing import Optional

from langchain import chains
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from langup import config


def LLMChain(
    system: str,
    human: str = '{text}'
):
    chat_model_kwargs = {
        'max_retries': 1,
        'request_timeout': 60,
        **config.auth.openai_kwargs,
    }
    chat_model = ChatOpenAI(**chat_model_kwargs)
    chat_prompt = ChatPromptTemplate.from_messages([
        ('system', system),
        ('human', human)
    ])
    config.auth.check_openai_config()
    return chat_prompt | chat_model
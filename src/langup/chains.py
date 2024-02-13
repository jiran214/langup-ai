from typing import Optional

from langchain_community.chat_models import ChatOpenAI
from langchain import chains
from langchain.prompts import ChatPromptTemplate
from langup import config


def LLMChain(
    system: str,
    human: str = '{text}',
    model="gpt-3.5-turbo",
    openai_api_key: str = None,
    openai_proxy: str = None,
    openai_api_base: str = None,
    temperature: int = 0.65,
    max_tokens: int = None,
    chat_model_kwargs: Optional[dict] = None
):
    config.auth.set_openai_config(openai_api_key, openai_proxy, openai_api_base)
    chat_model_kwargs = chat_model_kwargs or {}
    chat_model_kwargs.update(
        max_retries=1,
        request_timeout=60,
        temperature=temperature,
        max_tokens=max_tokens,
        model=model,
        **config.auth.openai_kwargs,
    )
    chat_model = ChatOpenAI(**chat_model_kwargs)
    chat_prompt = ChatPromptTemplate.from_messages([
        ('system', system),
        ('human', human)
    ])
    config.auth.check_openai_config()
    return chains.LLMChain(llm=chat_model, prompt=chat_prompt)
from typing import Literal, Iterable

from bilibili_api.dynamic import send_dynamic, BuildDynamic
from langchain_core.runnables import chain

from langup.listener.schema import SchedulingEvent
from langup import config, Process, runables


@chain
async def react(_content):
    await send_dynamic(BuildDynamic.create_by_args(text=_content), credential=config.credential)


def run(system, events: Iterable[SchedulingEvent], openai_api_key=None, openai_kwargs: dict = {}):
    process = Process()
    _chain = (
             runables.Prompt(system=system, human='{input}')
             | runables.LLM(openai_api_key, model_name="gpt-3.5-turbo", **openai_kwargs)
             | react
    )
    process.add_sche_thread(events, _chain)
    process.run()


if __name__ == '__main__':
    run(
        system='你是一个BiliBili up 主',
        events=[
            SchedulingEvent(input='请感谢大家的关注！', time='10m'),
            SchedulingEvent(input='请感谢大家的关注！', time='0:36')
        ]
    )
from pydantic import BaseModel


from langup.api.bilibili import sync
from langup.listener.bilibili import *


class TestModel(BaseModel):
    resp: str


api.credential = api.Credential(**{
    "sessdata": "a824317d%2C1710774575%2Ce58cf%2A91CjDpYi1UknFmgJkXiAPg-y_RpWNc73FLjyWNF8r9K5PqNBZ9e_M18bw85dy2Vyp1LjYSVlV5bTVEY2lhWC1DWXVpbmlTY0g5VnVNdURwYTFWSF9YTDZQYWpJeVNCTjFHRlpQMXFZVkl6SWdMOFl4bTJmV3NfemlUb2VJRU9UTVY5SHIwdEpVTFJRIIEC",
    "bili_jct": "15a331529e1396dc09116f25ad539225",
    "buvid3": "7FBCC946-3762-249F-5F44-A76F1737260657495infoc",
    "dedeuserid": "410282523",
    "ac_time_value": "ee742ca7c376a3faeff6de958d3e4a91"
})


def tSessionListener():
    # sync(SessionUnreadListener(
    #     mq_list=[],
    #     middlewares=[]
    # ).alisten())

    sync(SessionAtListener(
        mq_list=[],
        middlewares=[]
    ).alisten())


tSessionListener()
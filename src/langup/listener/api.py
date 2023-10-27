import queue
from typing import Optional, Literal, Type

from pip._internal.network.utils import raise_for_status
from pydantic import Field
from requests import Session, Response

from langup import base
import requests


class SyncAPIListener(base.Listener):
    session: Optional[Session] = Field(default=None)
    method: Literal['get', 'post'] = Field()
    url: str
    data: Optional[dict] = None
    json_data: Optional[dict] = None
    Schema: Type[Response] = Response

    async def _alisten(self):
        session = self.session or requests.request
        r = session.request(
            method=self.method,
            url=self.url,
            data=self.data,
            json=self.json_data,
        )
        raise_for_status(r)
        return r

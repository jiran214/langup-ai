from typing import Optional, Literal, Type, ClassVar

import requests
from pip._internal.network.utils import raise_for_status
from pydantic import Field
from requests import Response, Session

from langup import base


class SyncAPIReaction(base.Reaction):
    session: Optional[Session] = Field(default=None)
    method: Literal['get', 'post']
    url: str
    data: Optional[dict] = None
    json_data: Optional[dict] = None
    Schema: ClassVar = Response

    async def areact(self):
        session = self.session or requests.request
        r = session.request(
            method=self.method,
            url=self.url,
            data=self.data,
            json=self.json_data,
        )
        raise_for_status(r)
        return r

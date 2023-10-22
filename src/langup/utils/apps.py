from typing import List

from pydantic import BaseModel

from langup import base


class App:

    def __init__(self):
        ...

    def mount(self, uploader: base.Uploader, reaction_list: List[base.Reaction]):
        self.reaction_list = reaction_list

    def construct_schema(self):
        class Schema(BaseModel):
            ...
        return Schema

    def as_client(self):
        ...

    def as_server(self):
        ...
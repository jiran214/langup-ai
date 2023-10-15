import json
from datetime import datetime

from langup import config
from langup.utils.utils import Record


class ConfigImport:

    @classmethod
    def from_json_file(cls, json_path):
        json_data = json.load(fp=json_path, encoding='utf-8')
        up = cls(**json_data)
        return up


class Logger:

    @property
    def record_path(self):
        return f"{config.log['file_path']}{self.__class__.__name__}Record.txt"

    def record(self, listener_kwargs, time_cost, react_kwargs):
        rcd = Record(
            listener_kwargs=listener_kwargs,
            time_cost=time_cost,
            created_time=str(datetime.now()),
            react_kwargs=react_kwargs
        )
        if 'file' in config.log['console']:
            rcd.save_file(path=self.record_path)
        if 'print' in config.log['console']:
            rcd.print()

    def query(self):
        with open(self.record_path, 'a+', encoding='utf-8') as f:
            try:
                return json.loads('[' + ''.join(line for line in f.readlines()).replace('}\n{', '},{') + ']')
            except Exception as e:
                raise Exception(f'Record文件:{self.record_path}序列化失败,请确认是否手动修应该过\n{e}')

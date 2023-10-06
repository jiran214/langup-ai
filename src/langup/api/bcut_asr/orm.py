from enum import Enum
from typing import List, Tuple

from pydantic import BaseModel


class ASRDataSeg(BaseModel):
    '文字识别-断句'

    class ASRDataWords(BaseModel):
        '文字识别-逐字'
        label: str
        start_time: int
        end_time: int
        confidence: int

    start_time: int
    end_time: int
    transcript: str
    words: List[ASRDataWords]
    confidence: int

    def to_srt_ts(self) -> str:
        '转换为srt时间戳'

        def _conv(ms: int) -> Tuple[int, int, int, int]:
            return ms // 3600000, ms // 60000 % 60, ms // 1000 % 60, ms % 1000

        s_h, s_m, s_s, s_ms = _conv(self.start_time)
        e_h, e_m, e_s, e_ms = _conv(self.end_time)
        return f'{s_h:02d}:{s_m:02d}:{s_s:02d},{s_ms:03d} --> {e_h:02d}:{e_m:02d}:{e_s:02d},{e_ms:03d}'

    def to_lrc_ts(self) -> str:
        '转换为lrc时间戳'

        def _conv(ms: int) -> Tuple[int, int, int]:
            return ms // 60000, ms // 1000 % 60, ms % 1000 // 10

        s_m, s_s, s_ms = _conv(self.start_time)
        return f'[{s_m:02d}:{s_s:02d}.{s_ms:02d}]'


class ASRData(BaseModel):
    '语音识别结果'
    utterances: List[ASRDataSeg]
    version: str

    def __iter__(self):
        'iter穿透'
        return iter(self.utterances)

    def has_data(self) -> bool:
        '是否识别到数据'
        return len(self.utterances) > 0

    def to_txt(self) -> str:
        '转成txt格式字幕 (无时间标记)'
        return '\n'.join(
            seg.transcript
            for seg
            in self.utterances
        )

    def to_srt(self) -> str:
        '转成srt格式字幕'
        return '\n'.join(
            f'{n}\n{seg.to_srt_ts()}\n{seg.transcript}\n'
            for n, seg
            in enumerate(self.utterances, 1)
        )

    def to_lrc(self) -> str:
        '转成lrc格式字幕'
        return '\n'.join(
            f'{seg.to_lrc_ts()}{seg.transcript}'
            for seg
            in self.utterances
        )

    def to_ass(self) -> str:
        ...




class ResourceCreateRspSchema(BaseModel):
    """上传申请响应"""
    resource_id: str
    title: str
    type: int
    in_boss_key: str
    size: int
    upload_urls: List[str]
    upload_id: str
    per_size: int


class ResourceCompleteRspSchema(BaseModel):
    """上传提交响应"""
    resource_id: str
    download_url: str


class TaskCreateRspSchema(BaseModel):
    """任务创建响应"""
    resource: str
    result: str
    task_id: str  # 任务id


class ResultStateEnum(Enum):
    """任务状态枚举"""
    STOP = 0  # 未开始
    RUNING = 1  # 运行中
    ERROR = 3  # 错误
    COMPLETE = 4  # 完成


class ResultRspSchema(BaseModel):
    """任务结果查询响应"""
    task_id: str  # 任务id
    result: str  # 结果数据-json
    remark: str  # 任务状态详情
    state: ResultStateEnum  # 任务状态

    def parse(self) -> ASRData:
        """解析结果数据"""
        return ASRData.parse_raw(self.result)

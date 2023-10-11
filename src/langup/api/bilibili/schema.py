#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import List

from pydantic import BaseModel


class BiliNoteTag(BaseModel):
    # tag_id
    tag_id: int
    # TAG名称
    tag_name: str


class BiliNoteStat(BaseModel):
    # 稿件avid
    aid: int
    # 播放数
    view: int
    # 弹幕数
    danmaku: int
    # 评论数
    reply: int
    # 收藏数
    favorite: int
    # 投币数
    coin: int
    # 分享数
    share: int
    # 当前排名
    now_rank: int
    # 历史最高排行
    his_rank: int
    # 获赞数
    like: int


class BiliNoteView(BaseModel):
    # 稿件bvid
    bvid: str
    # 稿件avid
    aid: int
    # 稿件分P总数 默认为1
    videos: int
    # 分区tid
    tid: int  # 子分区名称
    tname: str  # 视频类型 1：原创 2：转载
    copyright: int
    # 稿件封面图片url
    pic: str
    # 稿件标题
    title: str  # 稿件发布时间 秒级时间戳
    pubdate: int
    # 用户投稿时间 秒级时间戳
    ctime: int
    # 视频简介
    desc: str  # 稿件总时长(所有分P) 单位为秒
    duration: int
    # 视频同步发布的的动态的文字内容
    dynamic: str
    # 视频1P cid
    cid: int
    # 视频状态数
    stat: BiliNoteStat
    # 视频UP主信息 # 包含mid、face、up name
    owner: dict
    # 视频CC字幕信息
    subtitle: dict = {}


class BiliNote(BaseModel):
    # 视频基本信息
    View: BiliNoteView
    # 视频TAG信息
    Tags: List[BiliNoteTag]
    # 推荐视频信息
    # Related: List[BiliNoteView]

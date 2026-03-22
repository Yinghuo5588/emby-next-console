"""统计模块 schemas — 简化为纯数据结构定义"""
from pydantic import BaseModel


class StatsOverview(BaseModel):
    total_plays: int = 0
    total_duration_sec: int = 0
    unique_users: int = 0
    today_plays: int = 0

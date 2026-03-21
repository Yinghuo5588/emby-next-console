from datetime import datetime
from pydantic import BaseModel
from typing import Any


class SettingItem(BaseModel):
    setting_key: str
    setting_group: str
    value: Any
    description: str | None


class SettingUpdateRequest(BaseModel):
    value: Any


class HealthResponse(BaseModel):
    status: str
    db: str
    redis: str


class JobRunItem(BaseModel):
    job_id: str
    job_type: str
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    error_message: str | None

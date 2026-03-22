from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel


class TemplateCreateRequest(BaseModel):
    name: str
    description: str | None = None
    library_access: list[str] | None = None
    policy_json: dict | None = None
    configuration_json: dict | None = None
    is_default: bool = False


class TemplateResponse(BaseModel):
    id: int
    name: str
    description: str | None
    library_access: list | None
    policy_json: dict | None
    configuration_json: dict | None
    is_default: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class TemplateListResponse(BaseModel):
    items: list[TemplateResponse]
    total: int
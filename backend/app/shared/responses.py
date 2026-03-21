from typing import Any, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "ok"
    data: T | None = None
    meta: dict[str, Any] = {}

    @classmethod
    def ok(cls, data: Any = None, message: str = "ok", meta: dict | None = None) -> "ApiResponse":
        return cls(success=True, message=message, data=data, meta=meta or {})

    @classmethod
    def error(cls, message: str, error_code: str = "ERROR") -> dict:
        return {"success": False, "message": message, "error_code": error_code, "details": {}}

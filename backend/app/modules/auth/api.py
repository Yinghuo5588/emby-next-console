"""auth API — Emby 管理员登录"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.emby import emby
from app.core.security import create_access_token
from app.core.exceptions import UnauthorizedError
from app.core.dependencies import get_current_user_payload

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    avatar_url: str = ""
    is_admin: bool = True


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    """用 Emby 账号登录（仅管理员）"""
    result = await emby.auth_with_password(body.username, body.password)
    if not result:
        raise UnauthorizedError("用户名或密码错误")

    user = result.get("User", {})
    access_token_raw = result.get("AccessToken", "")

    policy = user.get("Policy", {}) or {}
    if not policy.get("IsAdministrator", False):
        raise UnauthorizedError("仅管理员可登录")

    user_id = user.get("Id", "")
    username = user.get("Name", body.username)

    jwt_token = create_access_token(
        subject=user_id,
        emby_token=access_token_raw,
        username=username,
        is_admin=True,
    )

    primary_image_tag = user.get("PrimaryImageTag", "")
    avatar_url = f"/api/v1/manage/users/{user_id}/avatar" if primary_image_tag else ""

    return LoginResponse(
        access_token=jwt_token,
        user_id=user_id,
        username=username,
        avatar_url=avatar_url,
        is_admin=True,
    )


@router.get("/me")
async def me(payload: dict = Depends(get_current_user_payload)):
    return {
        "ok": True,
        "user_id": payload.get("sub"),
        "username": payload.get("username"),
        "is_admin": payload.get("is_admin", False),
    }

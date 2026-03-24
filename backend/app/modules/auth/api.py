"""auth API — Emby 管理员登录"""
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.emby import emby
from app.core.security import create_access_token
from app.core.exceptions import UnauthorizedError

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


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    """用 Emby 账号登录（仅管理员）"""
    result = await emby.auth_with_password(body.username, body.password)
    if not result:
        raise UnauthorizedError("用户名或密码错误")

    user = result.get("User", {})
    access_token_raw = result.get("AccessToken", "")

    # 检查是否是管理员
    policy = user.get("Policy", {}) or {}
    if not policy.get("IsAdministrator", False):
        raise UnauthorizedError("仅管理员可登录")

    user_id = user.get("Id", "")
    username = user.get("Name", body.username)

    # 生成自己的 JWT
    jwt_token = create_access_token(
        subject=user_id,
        emby_token=access_token_raw,
        username=username,
    )

    # 头像 URL
    primary_image_tag = user.get("PrimaryImageTag", "")
    avatar_url = f"/api/v1/proxy/user_image/{user_id}" if primary_image_tag else ""

    return LoginResponse(
        access_token=jwt_token,
        user_id=user_id,
        username=username,
        avatar_url=avatar_url,
    )


@router.get("/me")
async def me():
    """验证 token 有效性（前端刷新时用）"""
    # 实际校验由 dependencies.py 的 get_current_user_id 负责
    # 这里单独做一个简单版本：从 header 解析
    return {"ok": True}

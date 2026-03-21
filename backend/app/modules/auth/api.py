from fastapi import APIRouter, Depends

from app.db.session import AsyncSessionDep
from app.core.dependencies import get_current_user_id
from app.shared.responses import ApiResponse
from .schemas import LoginRequest, TokenResponse, MeResponse
from .service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(body: LoginRequest, db: AsyncSessionDep):
    service = AuthService(db)
    token = await service.login(body.username, body.password)
    return ApiResponse.ok(data=TokenResponse(access_token=token))


@router.get("/me", response_model=ApiResponse[MeResponse])
async def me(db: AsyncSessionDep, user_id: str = Depends(get_current_user_id)):
    service = AuthService(db)
    info = await service.get_user_info(user_id)
    return ApiResponse.ok(data=MeResponse(**info))


@router.post("/logout", response_model=ApiResponse)
async def logout(user_id: str = Depends(get_current_user_id)):
    return ApiResponse.ok(message="logged out")

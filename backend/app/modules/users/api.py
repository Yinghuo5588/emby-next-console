from fastapi import APIRouter, Depends, Query

from app.db.session import AsyncSessionDep
from app.core.dependencies import get_current_user_id
from app.shared.responses import ApiResponse
from .schemas import UserDetail, UserListResponse, UserUpdateRequest
from .service import UsersService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=ApiResponse[UserListResponse])
async def list_users(
    db: AsyncSessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: str = Depends(get_current_user_id),
):
    return ApiResponse.ok(data=await UsersService(db).list_users(page, page_size))


@router.get("/{user_id}", response_model=ApiResponse[UserDetail])
async def get_user(user_id: str, db: AsyncSessionDep, _: str = Depends(get_current_user_id)):
    return ApiResponse.ok(data=await UsersService(db).get_user(user_id))


@router.patch("/{user_id}", response_model=ApiResponse[UserDetail])
async def update_user(user_id: str, body: UserUpdateRequest, db: AsyncSessionDep, _: str = Depends(get_current_user_id)):
    return ApiResponse.ok(data=await UsersService(db).update_user(user_id, body))

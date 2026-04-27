from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.student import Student
from app.schemas.auth import (
    LoginRequest, WechatLoginRequest, LoginResponse,
    RefreshResponse, UserInfo, TokenResponse
)
from app.utils.auth import (
    verify_password, create_access_token,
    get_token_remaining_days, get_password_hash
)
from app.utils.wechat import get_wechat_openid
from app.dependencies import get_current_user
from app.config import settings

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """管理端账号密码登录"""
    result = await db.execute(
        select(User).where(User.username == request.username)
    )
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "用户名或密码错误"},
        )

    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "用户名或密码错误"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "USER_DISABLED", "message": "账号已被禁用"},
        )

    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=expires_delta,
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=int(expires_delta.total_seconds()),
        user={
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "display_name": user.display_name,
        }
    )


@router.post("/wechat", response_model=LoginResponse)
async def wechat_login(request: WechatLoginRequest, db: AsyncSession = Depends(get_db)):
    """小程序微信登录"""
    wechat_data = await get_wechat_openid(request.code)

    # 开发模式：若未配置微信，使用 code 作为 openid（仅开发调试用）
    if not wechat_data:
        if settings.DEBUG and request.code.startswith("test_"):
            openid = request.code.replace("test_", "")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "WECHAT_LOGIN_FAILED", "message": "微信登录失败，请重试"},
            )
    else:
        openid = wechat_data.get("openid")

    if not openid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "WECHAT_LOGIN_FAILED", "message": "未获取到微信 openid"},
        )

    # 查找已绑定的用户
    result = await db.execute(
        select(User).where(User.openid == openid)
    )
    user = result.scalar_one_or_none()

    display_name = "微信用户"
    avatar_url = None
    if request.user_info:
        display_name = request.user_info.get("nickName", "微信用户")
        avatar_url = request.user_info.get("avatarUrl")

    # 首次登录自动注册
    if not user:
        user = User(
            openid=openid,
            role="student",
            display_name=display_name,
            avatar_url=avatar_url,
            is_active=True,
        )
        db.add(user)
        await db.flush()
    else:
        # 更新微信信息
        if display_name:
            user.display_name = display_name
        if avatar_url:
            user.avatar_url = avatar_url

    await db.commit()
    await db.refresh(user)

    # 查找关联学生
    student_result = await db.execute(
        select(Student).where(
            (Student.user_id == user.id) | (Student.parent_user_id == user.id)
        ).where(Student.is_active == True)
    )
    student = student_result.scalar_one_or_none()

    expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role, "openid": openid},
        expires_delta=expires_delta,
    )

    user_info = {
        "id": user.id,
        "role": user.role,
        "display_name": user.display_name,
    }
    if student:
        user_info["student_id"] = student.id

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=int(expires_delta.total_seconds()),
        user=user_info,
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """刷新 Token"""
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_token = create_access_token(
        data={"sub": str(current_user.id), "role": current_user.role},
        expires_delta=expires_delta,
    )
    return RefreshResponse(
        access_token=new_token,
        expires_in=int(expires_delta.total_seconds()),
    )


@router.get("/me", response_model=UserInfo)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return UserInfo(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        display_name=current_user.display_name,
        avatar_url=current_user.avatar_url,
        phone=current_user.phone,
        is_active=current_user.is_active,
    )

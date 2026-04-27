from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError

from app.database import get_db
from app.models.user import User
from app.models.student import Student
from app.utils.auth import decode_token

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """获取当前已登录用户（必须登录）"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_MISSING", "message": "缺少认证 Token"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "TOKEN_INVALID", "message": "Token 格式无效"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_EXPIRED", "message": "Token 已过期或无效"},
        )

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "USER_NOT_FOUND", "message": "用户不存在或已被禁用"},
        )
    return user


async def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """仅管理员（老师）可访问"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "无权访问，仅管理员可操作"},
        )
    return current_user


async def get_student_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """学生或管理员可访问"""
    if current_user.role not in ("admin", "student", "parent"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "权限不足"},
        )
    return current_user


async def get_current_student(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Student:
    """
    获取当前登录用户对应的学生档案
    适用于小程序端（student/parent 角色）
    """
    if current_user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "此接口仅供学生/家长使用"},
        )

    if current_user.role == "student":
        result = await db.execute(
            select(Student).where(
                Student.user_id == current_user.id,
                Student.is_active == True
            )
        )
    else:  # parent
        result = await db.execute(
            select(Student).where(
                Student.parent_user_id == current_user.id,
                Student.is_active == True
            )
        )

    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "STUDENT_NOT_FOUND", "message": "未找到关联学生档案"},
        )
    return student

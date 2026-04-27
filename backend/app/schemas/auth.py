from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    username: str
    password: str


class WechatLoginRequest(BaseModel):
    code: str
    user_info: Optional[dict] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

    class Config:
        from_attributes = True


class LoginResponse(TokenResponse):
    user: dict


class RefreshResponse(BaseModel):
    access_token: str
    expires_in: int


class UserInfo(BaseModel):
    id: int
    username: Optional[str] = None
    role: str
    display_name: str
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True

"""用户认证相关 Pydantic 模型"""

from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=32,
        pattern=r"^[a-zA-Z0-9_一-鿿]+$",
        description="用户名：3-32字符，支持中英文、数字、下划线",
    )
    password: str = Field(..., min_length=6, max_length=128)
    confirm_password: str = Field(..., min_length=6, max_length=128)
    captcha_id: str = Field(..., description="验证码 ID")
    captcha_code: str = Field(..., description="验证码")


class UserLogin(BaseModel):
    username: str = Field(..., min_length=1, max_length=32)
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    is_active: int
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class CaptchaResponse(BaseModel):
    captcha_id: str
    captcha_image: str


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6, max_length=128)
    confirm_password: str = Field(..., min_length=6, max_length=128)

"""
Admin 认证依赖

支持两种认证方式：
1. 静态 Admin Token（Bearer token 字符串比对）
2. 管理员用户 JWT（解码后 role=admin）
"""

from fastapi import Header, HTTPException

from app.core.config import settings


async def verify_admin_token(authorization: str = Header(..., alias="Authorization")):
    """验证 Admin 权限：支持静态 Token 或管理员 JWT"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="无效的认证格式")

    token = authorization[7:]

    # 方式 1: 静态 Admin Token
    if settings.ADMIN_TOKEN and token == settings.ADMIN_TOKEN:
        return True

    # 方式 2: 管理员用户 JWT
    try:
        from app.core.security import decode_access_token
        payload = decode_access_token(token)
        if payload.get("role") == "admin":
            return True
    except Exception:
        pass

    raise HTTPException(status_code=401, detail="无管理权限")

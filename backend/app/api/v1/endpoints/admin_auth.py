"""
Admin Token 认证依赖
"""

from fastapi import Header, HTTPException

from app.core.config import settings


async def verify_admin_token(authorization: str = Header(..., alias="Authorization")):
    """验证 Admin Bearer Token"""
    if not settings.ADMIN_TOKEN:
        raise HTTPException(status_code=503, detail="Admin 未配置")
    if authorization != f"Bearer {settings.ADMIN_TOKEN}":
        raise HTTPException(status_code=401, detail="Token 无效")
    return True

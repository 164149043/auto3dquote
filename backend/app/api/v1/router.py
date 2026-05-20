"""v1 版本 API 路由注册"""

from fastapi import APIRouter

from app.api.v1.endpoints import admin, convert, health, materials, quote

api_router = APIRouter()

api_router.include_router(quote.router, tags=["quote"])
api_router.include_router(health.router, tags=["health"])
api_router.include_router(materials.router, tags=["materials"])
api_router.include_router(convert.router, tags=["convert"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

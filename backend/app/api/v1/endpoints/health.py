"""健康检查端点"""

from pathlib import Path

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/health", summary="健康检查")
async def health_check():
    """检查 API 和 PrusaSlicer 的可用状态"""
    slicer_available = Path(settings.PRUSA_SLICER_PATH).exists()
    return {
        "status": "ok",
        "prusa_slicer_available": slicer_available,
        "prusa_slicer_path": settings.PRUSA_SLICER_PATH,
    }

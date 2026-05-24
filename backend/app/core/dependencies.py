"""
FastAPI 依赖注入

将所有服务组装成 AnalysisPipeline 并注入到路由端点。
"""

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.database import get_db
from app.db.models import User
from app.services.config_service import config_service
from app.services.file_service import FileService
from app.services.gcode_parser import GCodeParserService
from app.services.mesh_analyzer import MeshAnalyzerService
from app.services.pipeline import AnalysisPipeline
from app.services.slicer_service import SlicerService


def get_settings():
    """返回全局配置单例"""
    return settings


def get_config_service():
    """返回配置缓存服务单例"""
    return config_service


def get_file_service() -> FileService:
    return FileService()


def get_mesh_analyzer() -> MeshAnalyzerService:
    return MeshAnalyzerService()


def get_slicer_service() -> SlicerService:
    return SlicerService()


def get_gcode_parser() -> GCodeParserService:
    return GCodeParserService()


def get_pipeline() -> AnalysisPipeline:
    """组装完整流水线"""
    return AnalysisPipeline(
        file_service=get_file_service(),
        mesh_analyzer=get_mesh_analyzer(),
        slicer=get_slicer_service(),
        gcode_parser=get_gcode_parser(),
    )


async def get_current_user(
    authorization: str = Header(..., alias="Authorization"),
    db: Session = Depends(get_db),
) -> User:
    """验证 JWT Bearer Token 并返回当前用户"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证格式",
        )
    token = authorization[7:]
    try:
        payload = decode_access_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌",
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证令牌已过期或无效",
        )

    user = db.query(User).filter(User.username == username).first()
    if user is None or user.is_active != 1:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已禁用",
        )
    return user

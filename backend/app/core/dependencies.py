"""
FastAPI 依赖注入

将所有服务组装成 AnalysisPipeline 并注入到路由端点。
"""

from app.core.config import settings
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

"""
网格分析服务

使用 trimesh 加载和分析 STL/OBJ 模型:
- 尺寸 (包围盒)
- 体积
- 表面积
- 三角形/顶点数
- 水密性检测
- 构建体积检查
"""

from pathlib import Path

import numpy as np
import trimesh

from app.services.config_service import config_service
from app.core.exceptions import MeshAnalysisError, ModelTooLargeError
from app.models.analysis import MeshAnalysisResult, MeshDimensions
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)


class MeshAnalyzerService:
    """基于 trimesh 的 3D 模型分析服务"""

    def analyze(self, file_path: Path, process: str = "fdm") -> MeshAnalysisResult:
        """
        执行完整的网格分析。

        1. 使用 trimesh 加载模型
        2. 检测水密性
        3. 提取尺寸、体积、表面积
        4. 检查是否超出打印机构建体积
        5. 对非水密网格使用包围盒近似体积
        """
        try:
            mesh = trimesh.load(str(file_path), force="mesh")
        except Exception as e:
            raise MeshAnalysisError(
                f"无法加载模型文件: {file_path.name}",
                detail=str(e),
            )

        warnings: list[str] = []
        file_size = file_path.stat().st_size

        # 提取包围盒尺寸
        extents = mesh.extents  # [x, y, z] mm
        dimensions = MeshDimensions(
            x_mm=round(float(extents[0]), 2),
            y_mm=round(float(extents[1]), 2),
            z_mm=round(float(extents[2]), 2),
        )

        # 检查是否超出设备构建体积
        volume_limits = config_service.MACHINE_VOLUME_MAX_MM.get(
            process, config_service.MACHINE_VOLUME_MAX_MM["fdm"]
        )
        if extents[0] > volume_limits["x"] or extents[1] > volume_limits["y"] or extents[2] > volume_limits["z"]:
            raise ModelTooLargeError(
                f"模型尺寸 ({dimensions.x_mm}x{dimensions.y_mm}x{dimensions.z_mm}mm) "
                f"超出 {process.upper()} 设备构建体积 ({volume_limits['x']}x{volume_limits['y']}x{volume_limits['z']}mm)",
                detail=f"extents={extents.tolist()}, process={process}",
            )

        # 水密性检测
        is_watertight = bool(mesh.is_watertight)

        # 体积计算 — 非水密时使用包围盒近似
        volume = self._get_volume(mesh, is_watertight, warnings)

        # 表面积
        surface_area = float(mesh.area) if hasattr(mesh, "area") else 0.0

        result = MeshAnalysisResult(
            is_watertight=is_watertight,
            volume_mm3=round(volume, 2),
            bounding_box=dimensions,
            surface_area_mm2=round(surface_area, 2),
            triangle_count=len(mesh.faces),
            vertex_count=len(mesh.vertices),
            file_size_bytes=file_size,
            warnings=warnings,
        )

        logger.info(
            "分析完成: %s, 水密=%s, 体积=%.1fmm³, 三角形=%d",
            file_path.name,
            is_watertight,
            volume,
            len(mesh.faces),
        )
        return result

    def _get_volume(self, mesh: trimesh.Trimesh, is_watertight: bool, warnings: list[str]) -> float:
        """
        获取模型体积。
        水密网格使用精确体积；非水密时使用包围盒体积并添加警告。
        """
        if is_watertight:
            return float(mesh.volume)
        else:
            warnings.append(
                "模型非水密 (non-manifold)，体积使用包围盒估算，实际耗材可能偏差较大"
            )
            return float(mesh.bounding_box.volume)

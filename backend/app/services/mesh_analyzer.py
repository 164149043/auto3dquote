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

        # 检查是否超出设备构建体积（考虑旋转摆放与重新定向）
        self._check_build_volume(mesh, dimensions, process, warnings)

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

    def _check_build_volume(
        self,
        mesh: trimesh.Trimesh,
        dimensions: MeshDimensions,
        process: str,
        warnings: list[str],
    ) -> None:
        """
        检查模型能否放入设备构建体积，按摆放精度依次尝试:

        1. 原始包围盒 (AABB) 直接放入
        2. AABB 旋转换轴放入 — 应对长边方向与设备大轴错开的情况
        3. 有向包围盒 (OBB) 放入 — 应对模型在文件内斜放、AABB 虚大的情况
        4. 均无法放入 → 报错，并提示可容纳该模型的其他工艺
        """
        all_limits = config_service.MACHINE_VOLUME_MAX_MM
        limits = all_limits.get(process, all_limits["fdm"])
        limit_xyz = (limits["x"], limits["y"], limits["z"])

        # 1. 原始朝向能放入
        if all(e <= lim for e, lim in zip(mesh.extents, limit_xyz)):
            return

        # 2. 旋转 90° 换轴后能放入
        if self._fits_rotation(mesh.extents, limit_xyz):
            warnings.append(
                f"模型原始朝向超出 {process.upper()} 设备构建体积，打印时旋转摆放后可放入"
            )
            return

        # 3. 文件内斜放的模型，尝试重新定向（PCA 主轴 + 绕 Z 轴旋转搜索）
        oriented = self._fits_reorientation(mesh, limit_xyz)
        if oriented is not None:
            warnings.append(
                f"模型在文件内摆放姿态不佳 (包围盒 {dimensions.x_mm}×{dimensions.y_mm}×{dimensions.z_mm}mm)，"
                f"按实际尺寸 ({oriented[0]:.0f}×{oriented[1]:.0f}×{oriented[2]:.0f}mm) "
                f"重新定向后可放入 {process.upper()} 设备构建体积"
            )
            return

        # 4. 均无法放入 → 找出能容纳该模型的其他工艺
        best_extents = self._best_oriented_extents(mesh)
        alternatives = [
            pid.upper()
            for pid, lim in all_limits.items()
            if pid != process and self._fits_rotation(best_extents, (lim["x"], lim["y"], lim["z"]))
        ]
        if alternatives:
            suggestion = f"，建议改用 {' / '.join(alternatives)} 工艺或拆件打印"
        else:
            suggestion = "，当前所有工艺均无法容纳，请考虑拆件或缩小模型"
        raise ModelTooLargeError(
            f"模型尺寸 ({dimensions.x_mm}×{dimensions.y_mm}×{dimensions.z_mm}mm) "
            f"即使旋转摆放也无法放入 {process.upper()} 设备构建体积 "
            f"({limits['x']}×{limits['y']}×{limits['z']}mm){suggestion}",
            detail=f"extents={mesh.extents.tolist()}, oriented_best={[round(e, 2) for e in best_extents]}, process={process}",
        )

    @staticmethod
    def _fits_rotation(extents, limit_xyz) -> bool:
        """判断三边旋转换轴后能否放入限制箱 — 两边排序后逐一对比即为最优轴向匹配"""
        return all(e <= lim for e, lim in zip(sorted(extents), sorted(limit_xyz)))

    def _fits_reorientation(self, mesh: trimesh.Trimesh, limit_xyz) -> list[float] | None:
        """
        尝试重新定向模型使其放入限制箱，返回首个可行朝向的三边（升序），不可行返回 None。

        两种互补策略:
        - PCA 主轴对齐: 应对细长件绕任意轴斜放
        - 绕 Z 轴 5° 步进旋转搜索: 应对模型在平台平面内斜放（含对称模型，PCA 对其失效）
        """
        v = self._sample_vertices(mesh)
        if v is None:
            return None

        # 策略 1: PCA 主轴对齐
        try:
            centered = v - v.mean(axis=0)
            _, axes = np.linalg.eigh(centered.T @ centered)
            proj = centered @ axes
            pca_extents = sorted((proj.max(axis=0) - proj.min(axis=0)).tolist())
            if self._fits_rotation(pca_extents, limit_xyz):
                return pca_extents
        except np.linalg.LinAlgError as e:
            logger.debug("PCA 主轴计算失败: %s", e)

        # 策略 2: 绕 Z 轴旋转搜索（包围盒以 180° 为周期）
        for deg in range(0, 180, 5):
            theta = np.radians(deg)
            rot = np.array([[np.cos(theta), np.sin(theta)], [-np.sin(theta), np.cos(theta)]])
            proj = np.concatenate([v[:, :2] @ rot, v[:, 2:3]], axis=1)
            extents = sorted((proj.max(axis=0) - proj.min(axis=0)).tolist())
            if self._fits_rotation(extents, limit_xyz):
                return extents
        return None

    def _best_oriented_extents(self, mesh: trimesh.Trimesh) -> list[float]:
        """
        估算模型重新定向后能达到的最优三边（升序），用于提示可容纳的替代工艺。

        在 AABB、PCA 主轴对齐、绕 Z 旋转最优朝向中取最长边最小者。
        """
        extents = [sorted(float(e) for e in mesh.extents)]
        v = self._sample_vertices(mesh)
        if v is not None:
            try:
                centered = v - v.mean(axis=0)
                _, axes = np.linalg.eigh(centered.T @ centered)
                proj = centered @ axes
                extents.append(sorted((proj.max(axis=0) - proj.min(axis=0)).tolist()))
            except np.linalg.LinAlgError:
                pass
            z_best = None
            for deg in range(0, 180, 5):
                theta = np.radians(deg)
                rot = np.array([[np.cos(theta), np.sin(theta)], [-np.sin(theta), np.cos(theta)]])
                proj = np.concatenate([v[:, :2] @ rot, v[:, 2:3]], axis=1)
                e = sorted((proj.max(axis=0) - proj.min(axis=0)).tolist())
                if z_best is None or e[2] < z_best[2]:
                    z_best = e
            if z_best is not None:
                extents.append(z_best)
        return min(extents, key=lambda e: (e[2], e[1]))

    @staticmethod
    def _sample_vertices(mesh: trimesh.Trimesh, max_samples: int = 20000) -> np.ndarray | None:
        """
        抽取网格顶点（float64）。顶点过多时抽样 — 包围盒由极值点决定，抽样误差可忽略。
        固定随机种子保证结果可复现。
        """
        try:
            v = np.asarray(mesh.vertices, dtype=np.float64)
        except Exception as e:
            logger.debug("顶点抽样失败: %s", e)
            return None
        if len(v) > max_samples:
            v = np.random.default_rng(0).choice(v, size=max_samples, replace=False)
        return v

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

"""
PrusaSlicer CLI 切片服务

调用 PrusaSlicer CLI 执行模型切片，生成 G-code。
使用 subprocess.run + asyncio.to_thread，兼容 Windows 事件循环。

注意: PrusaSlicer --load 加载 ini 时不会应用自定义 [print:...] section 的参数，
因此通过 CLI 参数显式覆盖层高等关键打印设置。
"""

import asyncio
import subprocess
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import SlicerError, SlicerTimeoutError
from app.models.common import QualityPreset
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)

# 质量预设对应的 CLI 覆盖参数
QUALITY_OVERRIDES: dict[QualityPreset, dict[str, str]] = {
    QualityPreset.DRAFT: {
        "layer-height": "0.3",
        "first-layer-height": "0.35",
        "perimeters": "2",
        "top-solid-layers": "3",
        "bottom-solid-layers": "2",
        "fill-density": "15%",
        "perimeter-speed": "70",
        "infill-speed": "100",
    },
    QualityPreset.STANDARD: {
        "layer-height": "0.2",
        "first-layer-height": "0.3",
        "perimeters": "3",
        "top-solid-layers": "4",
        "bottom-solid-layers": "3",
        "fill-density": "20%",
        "perimeter-speed": "60",
        "infill-speed": "80",
    },
    QualityPreset.HIGH: {
        "layer-height": "0.1",
        "first-layer-height": "0.2",
        "perimeters": "4",
        "top-solid-layers": "7",
        "bottom-solid-layers": "5",
        "fill-density": "25%",
        "perimeter-speed": "40",
        "infill-speed": "60",
    },
}


class SlicerService:
    """PrusaSlicer CLI 集成服务"""

    def __init__(self):
        self.slicer_path = Path(settings.PRUSA_SLICER_PATH)
        self.timeout = settings.PRUSA_SLICER_TIMEOUT
        self.profiles_dir = Path(settings.PRUSA_PROFILES_DIR)

    async def slice_model(
        self,
        stl_path: Path,
        output_path: Path,
        material: str = "PLA",
        quality: QualityPreset = QualityPreset.STANDARD,
    ) -> Path:
        """
        调用 PrusaSlicer CLI 执行切片。

        参数:
            stl_path: 输入的 STL/OBJ 文件路径
            output_path: 输出的 G-code 文件路径
            material: 材料类型
            quality: 质量预设

        返回: 生成的 G-code 文件路径
        抛出: SlicerError, SlicerTimeoutError
        """
        # 检查 PrusaSlicer 是否存在
        if not self.slicer_path.exists():
            raise SlicerError(
                f"PrusaSlicer 未找到: {self.slicer_path}",
                detail="请检查 .env 中的 PRUSA_SLICER_PATH 配置",
            )

        # 解析配置文件路径
        profile_path = self._resolve_profile_path(material, quality)

        # 构建 CLI 命令 — 使用列表传参避免空格问题
        cmd = [
            str(self.slicer_path),
            "--load", str(profile_path),
        ]

        # 通过 CLI 参数显式覆盖打印质量设置
        # PrusaSlicer --load 不加载自定义 [print:...] section，必须用 CLI 参数
        speed_factor = self._get_speed_factor(material)
        for key, value in QUALITY_OVERRIDES[quality].items():
            if "speed" in key:
                v = max(10, int(float(value) * speed_factor))
                cmd.extend([f"--{key}", str(v)])
            else:
                cmd.extend([f"--{key}", value])

        cmd.extend([
            "--export-gcode",
            "--output", str(output_path),
            str(stl_path),
        ])

        logger.info(
            "开始切片: %s (profile: %s, quality: %s, material: %s)",
            stl_path.name, profile_path.name, quality.value, material,
        )

        try:
            stdout, stderr, returncode = await asyncio.to_thread(
                self._run_subprocess, cmd
            )
        except subprocess.TimeoutExpired:
            raise SlicerTimeoutError(
                f"切片超时 ({self.timeout}秒): {stl_path.name}",
                detail=f"command: {' '.join(cmd)}",
            )
        except Exception as e:
            raise SlicerError(f"切片进程执行失败: {stl_path.name}", detail=str(e))

        if returncode != 0:
            raise SlicerError(
                f"PrusaSlicer 切片失败 (退出码 {returncode}): {stl_path.name}",
                detail=stderr[:2000] if stderr else stdout[:2000],
            )

        # 验证输出文件存在
        if not output_path.exists():
            raise SlicerError(
                f"切片完成但 G-code 文件未生成: {output_path}",
                detail=stdout[:2000],
            )

        file_size = output_path.stat().st_size
        logger.info("切片完成: %s (%.1f KB)", output_path.name, file_size / 1024)
        return output_path

    def _get_speed_factor(self, material: str) -> float:
        """不同材料的速度系数（TPU 必须慢，ABS 稍慢等）"""
        factors = {
            "PLA": 1.0,
            "PETG": 0.85,
            "ABS": 0.8,
            "TPU": 0.5,
            "NYLON": 0.75,
        }
        return factors.get(material, 1.0)

    def _resolve_profile_path(self, material: str, quality: QualityPreset) -> Path:
        """
        解析切片配置文件路径。
        格式: profiles_dir/{material}_{quality}.ini
        找不到时回退到 pla_standard.ini
        """
        target = self.profiles_dir / f"{material.lower()}_{quality.value}.ini"
        if target.exists():
            return target

        fallback = self.profiles_dir / "pla_standard.ini"
        if fallback.exists():
            logger.warning("配置文件 %s 不存在，回退到 %s", target, fallback)
            return fallback

        raise SlicerError(
            f"找不到任何切片配置文件 (尝试: {target}, 回退: {fallback})",
            detail=f"profiles_dir={self.profiles_dir}",
        )

    def _run_subprocess(self, cmd: list[str]) -> tuple[str, str, int]:
        """
        同步执行子进程 (通过 asyncio.to_thread 在线程池中运行，不阻塞事件循环)。

        返回: (stdout, stderr, returncode)
        """
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=self.timeout,
        )
        stdout = result.stdout.decode("utf-8", errors="replace")
        stderr = result.stderr.decode("utf-8", errors="replace")
        return stdout, stderr, result.returncode

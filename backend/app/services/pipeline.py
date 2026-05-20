"""
分析流水线编排器

串联所有服务，按顺序执行完整的上传-分析-切片-报价流程:
  验证上传 → 保存临时文件 → 网格分析 → 切片(仅FDM) → G-code 解析 → 报价计算 → 清理
"""

import time
import traceback
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.models.common import (
    DeliveryOption,
    PostProcessType,
    ProcessType,
    QualityPreset,
)
from app.models.quote import QuoteResponse
from app.services.file_service import FileService
from app.services.gcode_parser import GCodeParserService
from app.services.mesh_analyzer import MeshAnalyzerService
from app.services.pricing.factory import PricingStrategyFactory
from app.services.slicer_service import SlicerService
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)


class AnalysisPipeline:
    """完整分析流水线编排器"""

    def __init__(
        self,
        file_service: FileService,
        mesh_analyzer: MeshAnalyzerService,
        slicer: SlicerService,
        gcode_parser: GCodeParserService,
    ):
        self.file_service = file_service
        self.mesh_analyzer = mesh_analyzer
        self.slicer = slicer
        self.gcode_parser = gcode_parser

    async def execute(
        self,
        file: UploadFile,
        process: ProcessType = ProcessType.FDM,
        material: str = "PLA",
        quality: QualityPreset = QualityPreset.STANDARD,
        quantity: int = 1,
        post_processing: list[PostProcessType] | None = None,
        delivery: DeliveryOption = DeliveryOption.STANDARD,
    ) -> QuoteResponse:
        start_time = time.time()
        stl_path: Path | None = None
        original_path: Path | None = None
        gcode_path: Path | None = None
        all_warnings: list[str] = []

        try:
            # 验证并保存文件
            data, safe_name = await self.file_service.validate_upload(file)
            stl_path = self.file_service.save_temp_file(data, safe_name)

            # STEP/STP 文件需先转换为 STL 才能分析和切片
            original_path = stl_path
            if stl_path.suffix.lower() in (".step", ".stp"):
                stl_path = self._convert_step_to_stl(stl_path)

            # 网格分析
            analysis = self.mesh_analyzer.analyze(stl_path, process=process.value)
            all_warnings.extend(analysis.warnings)

            # 切片 → 解析 → 报价
            slicing_result = None
            quote_result = None
            status = "partial"

            # 仅 FDM 工艺使用 PrusaSlicer 切片
            if process == ProcessType.FDM:
                try:
                    gcode_path = stl_path.with_suffix(".gcode")
                    gcode_path = await self.slicer.slice_model(
                        stl_path, gcode_path, material, quality
                    )
                    slicing_result = self.gcode_parser.parse(gcode_path, material)
                except Exception as e:
                    tb = traceback.format_exc()
                    all_warnings.append(f"切片失败: {e}")
                    logger.warning("切片降级: %s\n%s", e, tb)

            # 报价计算（使用策略工厂）
            try:
                strategy = PricingStrategyFactory.get(process)
                quote_result = strategy.calculate(
                    analysis=analysis,
                    slicing=slicing_result,
                    material=material,
                    quantity=quantity,
                    post_processing=post_processing,
                    delivery=delivery,
                )
                status = "success"
            except Exception as e:
                tb = traceback.format_exc()
                all_warnings.append(f"报价计算失败: {e}")
                logger.warning("报价降级: %s\n%s", e, tb)
                status = "partial"

            if all_warnings and status == "success":
                status = "warning"

            elapsed = time.time() - start_time

            return QuoteResponse(
                status=status,
                analysis=analysis,
                slicing=slicing_result,
                quote=quote_result,
                warnings=all_warnings,
                processing_time_seconds=round(elapsed, 2),
            )

        finally:
            # 清理：原始上传文件 + 转换后的 STL + G-code
            paths_to_clean = [p for p in (original_path, stl_path, gcode_path) if p]
            self.file_service.cleanup(*paths_to_clean)

    def _convert_step_to_stl(self, step_path: Path) -> Path:
        """使用 gmsh 将 STEP 文件转换为 STL"""
        import gmsh

        stl_path = step_path.with_suffix(".stl")

        gmsh.initialize()
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.option.setNumber("Mesh.MeshSizeMin", 0.5)
        gmsh.option.setNumber("Mesh.MeshSizeMax", 5.0)
        gmsh.merge(str(step_path))
        gmsh.model.occ.synchronize()
        gmsh.model.mesh.generate(2)
        gmsh.write(str(stl_path))
        gmsh.finalize()

        logger.info("STEP→STL: %s → %s", step_path.name, stl_path.name)
        return stl_path

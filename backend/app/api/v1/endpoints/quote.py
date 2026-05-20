"""报价端点 — 核心接口，上传 3D 模型获取报价"""

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse

from app.services.config_service import config_service
from app.core.dependencies import get_pipeline
from app.models.common import DeliveryOption, PostProcessType, ProcessType, QualityPreset
from app.models.quote import QuoteResponse
from app.services.pipeline import AnalysisPipeline

router = APIRouter()


@router.post("/quote", response_model=QuoteResponse, summary="上传 3D 模型获取报价")
async def create_quote(
    file: UploadFile = File(..., description="3D 模型文件 (.stl/.obj/.3mf/.stp/.step)"),
    process: str = Form("fdm", description="工艺类型: fdm/sla/sls/mjf/cnc"),
    material: str = Form("PLA", description="材料类型"),
    quality: str = Form("standard", description="打印质量: draft/standard/high"),
    quantity: int = Form(1, ge=1, le=1000, description="打印数量"),
    post_processing: str = Form("", description="后处理选项，逗号分隔: sanding,painting"),
    delivery: str = Form("standard", description="交期: standard/express/urgent"),
    paint_options: str = Form("", description='喷漆子选项 JSON: {"finish":"matte","color":"#FF0000"}'),
    pipeline: AnalysisPipeline = Depends(get_pipeline),
):
    """
    接收 3D 模型文件，执行自动分析和报价。

    流程: 文件验证 → 网格分析 → 切片(仅FDM) → 报价计算

    支持多种工艺: FDM / SLA / SLS / MJF / CNC
    """
    proc = ProcessType(process.lower())
    qual = QualityPreset(quality.lower())
    deliv = DeliveryOption(delivery.lower())

    # 校验：材料必须属于所选工艺（动态配置，支持管理后台新增材料）
    valid_materials = config_service.PROCESS_MATERIALS.get(proc.value, [])
    if material not in valid_materials:
        return JSONResponse(
            status_code=400,
            content={
                "error": "InvalidParameter",
                "message": f"材料 {material} 不适用于 {proc.value} 工艺，可选: {', '.join(valid_materials)}",
                "detail": None,
            },
        )

    pp_list = []
    if post_processing.strip():
        valid_pp = config_service.PROCESS_POST_PROCESS.get(proc.value, [])
        for item in post_processing.split(","):
            item = item.strip()
            if item:
                pp = PostProcessType(item)
                if item in valid_pp:
                    pp_list.append(pp)

    return await pipeline.execute(file, proc, material, qual, quantity, pp_list or None, deliv)

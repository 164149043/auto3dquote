"""报价端点 — 核心接口，上传 3D 模型获取报价"""

import json

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_pipeline
from app.db.database import get_db
from app.db.models import QuoteRecord, User
from app.services.config_service import config_service
from app.models.common import DeliveryOption, PostProcessType, ProcessType, QualityPreset
from app.models.quote import QuoteResponse
from app.services.pipeline import AnalysisPipeline
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)

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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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

    result = await pipeline.execute(file, proc, material, qual, quantity, pp_list or None, deliv)

    # 保存报价记录（不影响返回）
    try:
        q = result.quote
        a = result.analysis
        s = result.slicing
        record = QuoteRecord(
            user_id=current_user.id,
            filename=file.filename or "unknown",
            process=proc.value,
            material=material,
            quality=qual.value,
            quantity=quantity,
            delivery=deliv.value,
            post_processing=post_processing if post_processing.strip() else None,
            status=result.status,
            unit_price=q.unit_price if q else 0,
            total_price=q.total_price if q else 0,
            material_cost=q.material_cost.subtotal if q and q.material_cost else 0,
            time_cost=q.time_cost.subtotal if q and q.time_cost else 0,
            post_process_cost=sum(p.subtotal for p in q.post_process_costs) if q else 0,
            delivery_surcharge=q.delivery_surcharge if q else 0,
            difficulty_surcharge=q.difficulty_surcharge if q else 0,
            support_cost=q.support_cost if q else 0,
            quantity_discount=q.quantity_discount if q else 0,
            volume_mm3=a.volume_mm3 if a else 0,
            surface_area_mm2=a.surface_area_mm2 if a else 0,
            bounding_box=json.dumps({
                "x": a.bounding_box.x_mm,
                "y": a.bounding_box.y_mm,
                "z": a.bounding_box.z_mm,
            }) if a else None,
            file_size_bytes=a.file_size_bytes if a else None,
            print_time_seconds=s.print_time_seconds if s else None,
            filament_used_grams=s.filament_used_grams if s else None,
            processing_time_seconds=result.processing_time_seconds,
        )
        db.add(record)
        db.commit()
    except Exception as e:
        logger.warning("报价记录保存失败: %s", e)
        db.rollback()

    return result

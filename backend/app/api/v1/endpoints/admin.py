"""
Admin 配置管理端点 — 材料增删改查、后处理、交期、映射、设置
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import (
    DeliveryOption,
    GlobalSetting,
    MachineVolumeLimit,
    Material,
    PostProcess,
    ProcessMaterial,
    ProcessPostProcess,
)
from app.api.v1.endpoints.admin_auth import verify_admin_token
from app.services.config_service import config_service

# 材料图片存储目录
MATERIAL_IMAGE_DIR = Path(__file__).parent.parent.parent.parent.parent / "data" / "material_images"

router = APIRouter(dependencies=[Depends(verify_admin_token)])


# ==================== Pydantic 请求模型 ====================

class MaterialInput(BaseModel):
    id: str
    label: str
    price: float
    unit: str = "g"
    density: float
    process: str
    machine_rate: float | None = None
    category: str | None = None
    description: str | None = None
    sort_order: int = 0

class MaterialUpdate(BaseModel):
    label: str | None = None
    price: float | None = None
    unit: str | None = None
    density: float | None = None
    machine_rate: float | None = None
    category: str | None = None
    description: str | None = None
    sort_order: int | None = None

class PostProcessInput(BaseModel):
    id: str
    label: str
    mode: str  # "fixed" / "percentage"
    value: float
    description: str | None = None

class PostProcessUpdate(BaseModel):
    label: str | None = None
    mode: str | None = None
    value: float | None = None
    description: str | None = None

class DeliveryOptionUpdate(BaseModel):
    label: str | None = None
    multiplier: float | None = None
    days: int | None = None
    sort_order: int | None = None

class ProcessMappingInput(BaseModel):
    material_ids: list[str]

class ProcessPostProcessMappingInput(BaseModel):
    post_process_ids: list[str]

class MachineLimitInput(BaseModel):
    max_x: float
    max_y: float
    max_z: float

class SettingInput(BaseModel):
    value: str  # JSON 字符串
    description: str | None = None


def _refresh():
    config_service.refresh()


# ==================== 完整配置快照 ====================

@router.get("/config", summary="获取完整配置快照")
async def get_full_config():
    return {
        "materials": config_service.MATERIAL_PRICING,
        "process_materials": config_service.PROCESS_MATERIALS,
        "post_processes": config_service.POST_PROCESS_PRICING,
        "process_post_processes": config_service.PROCESS_POST_PROCESS,
        "delivery_surcharge": config_service.DELIVERY_SURCHARGE,
        "machine_volume_limits": config_service.MACHINE_VOLUME_MAX_MM,
        "time_cost_per_hour": config_service.TIME_COST_PER_HOUR,
        "base_markup_rate": config_service.BASE_MARKUP_RATE,
        "cnc_setup_fee": config_service.CNC_SETUP_FEE,
        "cnc_minimum_order": config_service.CNC_MINIMUM_ORDER,
    }


# ==================== 材料 CRUD ====================

@router.get("/materials", summary="列出所有材料")
async def list_materials(db: Session = Depends(get_db)):
    materials = db.query(Material).order_by(Material.process, Material.sort_order).all()
    return [{"id": m.id, "label": m.label, "price": m.price, "unit": m.unit,
             "density": m.density, "process": m.process, "machine_rate": m.machine_rate,
             "category": m.category, "image_url": m.image_url, "description": m.description,
             "sort_order": m.sort_order} for m in materials]


@router.post("/materials", summary="创建材料")
async def create_material(data: MaterialInput, db: Session = Depends(get_db)):
    if db.query(Material).get(data.id):
        raise HTTPException(400, f"材料 {data.id} 已存在")
    now = datetime.now().isoformat()
    m = Material(**data.model_dump(), created_at=now, updated_at=now)
    db.add(m)
    # 同时添加到工艺映射，sort_order 取当前映射列表长度（追加到末尾）
    existing_count = db.query(ProcessMaterial).filter(
        ProcessMaterial.process_id == data.process
    ).count()
    db.add(ProcessMaterial(process_id=data.process, material_id=data.id, sort_order=existing_count))
    db.commit()
    _refresh()
    return {"ok": True, "id": data.id}


@router.put("/materials/{material_id}", summary="更新材料")
async def update_material(material_id: str, data: MaterialUpdate, db: Session = Depends(get_db)):
    m = db.query(Material).get(material_id)
    if not m:
        raise HTTPException(404, f"材料 {material_id} 不存在")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(m, key, val)
    m.updated_at = datetime.now().isoformat()
    db.commit()
    _refresh()
    return {"ok": True}


@router.delete("/materials/{material_id}", summary="删除材料")
async def delete_material(material_id: str, db: Session = Depends(get_db)):
    m = db.query(Material).get(material_id)
    if not m:
        raise HTTPException(404, f"材料 {material_id} 不存在")
    # 删除关联映射
    db.query(ProcessMaterial).filter(ProcessMaterial.material_id == material_id).delete()
    db.delete(m)
    db.commit()
    _refresh()
    return {"ok": True}


# ==================== 后处理 CRUD ====================

@router.get("/post-processes", summary="列出所有后处理")
async def list_post_processes(db: Session = Depends(get_db)):
    pps = db.query(PostProcess).all()
    return [{"id": p.id, "label": p.label, "mode": p.mode, "value": p.value,
             "description": p.description} for p in pps]


@router.post("/post-processes", summary="创建后处理")
async def create_post_process(data: PostProcessInput, db: Session = Depends(get_db)):
    if db.query(PostProcess).get(data.id):
        raise HTTPException(400, f"后处理 {data.id} 已存在")
    now = datetime.now().isoformat()
    db.add(PostProcess(**data.model_dump(), created_at=now, updated_at=now))
    db.commit()
    _refresh()
    return {"ok": True, "id": data.id}


@router.put("/post-processes/{pp_id}", summary="更新后处理")
async def update_post_process(pp_id: str, data: PostProcessUpdate, db: Session = Depends(get_db)):
    p = db.query(PostProcess).get(pp_id)
    if not p:
        raise HTTPException(404, f"后处理 {pp_id} 不存在")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(p, key, val)
    p.updated_at = datetime.now().isoformat()
    db.commit()
    _refresh()
    return {"ok": True}


@router.delete("/post-processes/{pp_id}", summary="删除后处理")
async def delete_post_process(pp_id: str, db: Session = Depends(get_db)):
    p = db.query(PostProcess).get(pp_id)
    if not p:
        raise HTTPException(404, f"后处理 {pp_id} 不存在")
    db.query(ProcessPostProcess).filter(ProcessPostProcess.post_process_id == pp_id).delete()
    db.delete(p)
    db.commit()
    _refresh()
    return {"ok": True}


# ==================== 交期选项 ====================

@router.get("/delivery-options", summary="列出交期选项")
async def list_delivery_options(db: Session = Depends(get_db)):
    opts = db.query(DeliveryOption).order_by(DeliveryOption.sort_order).all()
    return [{"id": d.id, "label": d.label, "multiplier": d.multiplier, "days": d.days} for d in opts]


@router.put("/delivery-options/{opt_id}", summary="更新交期选项")
async def update_delivery_option(opt_id: str, data: DeliveryOptionUpdate, db: Session = Depends(get_db)):
    d = db.query(DeliveryOption).get(opt_id)
    if not d:
        raise HTTPException(404, f"交期选项 {opt_id} 不存在")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(d, key, val)
    d.updated_at = datetime.now().isoformat()
    db.commit()
    _refresh()
    return {"ok": True}


# ==================== 工艺映射 ====================

@router.get("/process-mapping", summary="获取所有工艺映射")
async def get_process_mappings():
    return {
        "process_materials": config_service.PROCESS_MATERIALS,
        "process_post_processes": config_service.PROCESS_POST_PROCESS,
    }


@router.put("/process-mapping/{process_id}/materials", summary="更新工艺-材料映射")
async def update_process_materials(process_id: str, data: ProcessMappingInput, db: Session = Depends(get_db)):
    db.query(ProcessMaterial).filter(ProcessMaterial.process_id == process_id).delete()
    for idx, mat_id in enumerate(data.material_ids):
        db.add(ProcessMaterial(process_id=process_id, material_id=mat_id, sort_order=idx))
    db.commit()
    _refresh()
    return {"ok": True}


@router.put("/process-mapping/{process_id}/post-processes", summary="更新工艺-后处理映射")
async def update_process_post_processes(process_id: str, data: ProcessPostProcessMappingInput, db: Session = Depends(get_db)):
    db.query(ProcessPostProcess).filter(ProcessPostProcess.process_id == process_id).delete()
    for idx, pp_id in enumerate(data.post_process_ids):
        db.add(ProcessPostProcess(process_id=process_id, post_process_id=pp_id, sort_order=idx))
    db.commit()
    _refresh()
    return {"ok": True}


# ==================== 设备体积限制 ====================

@router.get("/machine-limits", summary="获取设备体积限制")
async def get_machine_limits(db: Session = Depends(get_db)):
    limits = db.query(MachineVolumeLimit).all()
    return [{"process_id": l.process_id, "max_x": l.max_x, "max_y": l.max_y, "max_z": l.max_z} for l in limits]


@router.put("/machine-limits/{process_id}", summary="更新设备体积限制")
async def update_machine_limits(process_id: str, data: MachineLimitInput, db: Session = Depends(get_db)):
    limit = db.query(MachineVolumeLimit).get(process_id)
    if limit:
        limit.max_x = data.max_x
        limit.max_y = data.max_y
        limit.max_z = data.max_z
    else:
        db.add(MachineVolumeLimit(process_id=process_id, **data.model_dump()))
    db.commit()
    _refresh()
    return {"ok": True}


# ==================== 全局设置 ====================

@router.get("/settings", summary="获取全局设置")
async def get_settings_api(db: Session = Depends(get_db)):
    settings_list = db.query(GlobalSetting).all()
    return [{"key": s.key, "value": json.loads(s.value), "description": s.description} for s in settings_list]


@router.put("/settings/{key}", summary="更新全局设置")
async def update_setting(key: str, data: SettingInput, db: Session = Depends(get_db)):
    s = db.query(GlobalSetting).get(key)
    if not s:
        db.add(GlobalSetting(key=key, value=data.value, description=data.description,
                             updated_at=datetime.now().isoformat()))
    else:
        s.value = data.value
        if data.description is not None:
            s.description = data.description
        s.updated_at = datetime.now().isoformat()
    db.commit()
    _refresh()
    return {"ok": True}


# ==================== 材料图片上传 ====================

@router.post("/materials/{material_id}/image", summary="上传材料示例图片")
async def upload_material_image(
    material_id: str,
    file: UploadFile = File(..., description="材料图片 (jpg/png/webp)"),
    db: Session = Depends(get_db),
):
    m = db.query(Material).get(material_id)
    if not m:
        raise HTTPException(404, f"材料 {material_id} 不存在")

    ext = os.path.splitext(file.filename or "image.jpg")[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".webp"):
        raise HTTPException(400, "仅支持 jpg/png/webp 格式")

    MATERIAL_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{material_id}{ext}"
    filepath = MATERIAL_IMAGE_DIR / filename

    content = await file.read()
    filepath.write_bytes(content)

    m.image_url = f"/static/materials/{filename}"
    m.updated_at = datetime.now().isoformat()
    db.commit()
    _refresh()
    return {"ok": True, "image_url": m.image_url}


# ==================== 缓存刷新 ====================

@router.post("/cache/refresh", summary="强制刷新配置缓存")
async def refresh_cache():
    _refresh()
    return {"ok": True, "message": "缓存已刷新"}

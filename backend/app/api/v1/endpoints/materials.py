"""材料与选项列表端点 — 返回完整工艺-材料-后处理-交期选项树"""

from fastapi import APIRouter

from app.services.config_service import config_service

router = APIRouter()

PROCESS_LABELS = {
    "fdm": "FDM 3D打印",
    "sla": "SLA 光固化",
    "sls": "SLS 激光烧结",
    "mjf": "MJF 多射流熔融",
    "cnc": "CNC 数控加工",
}

QUALITY_OPTIONS = {
    "fdm": [
        {"id": "draft", "label": "草稿", "desc": "0.3mm 层高"},
        {"id": "standard", "label": "标准", "desc": "0.2mm 层高"},
        {"id": "high", "label": "高质量", "desc": "0.1mm 层高"},
    ],
    "sla": [
        {"id": "draft", "label": "草稿", "desc": "0.1mm 层高"},
        {"id": "standard", "label": "标准", "desc": "0.05mm 层高"},
        {"id": "high", "label": "高质量", "desc": "0.025mm 层高"},
    ],
    "sls": [
        {"id": "standard", "label": "标准", "desc": "0.1mm 粉层"},
        {"id": "high", "label": "精细", "desc": "0.06mm 粉层"},
    ],
    "mjf": [
        {"id": "standard", "label": "标准", "desc": "0.08mm 层厚"},
        {"id": "high", "label": "精细", "desc": "0.04mm 层厚"},
    ],
    "cnc": [
        {"id": "draft", "label": "粗加工", "desc": "Ra 3.2"},
        {"id": "standard", "label": "标准", "desc": "Ra 1.6"},
        {"id": "high", "label": "精加工", "desc": "Ra 0.8"},
    ],
}


@router.get("/materials", summary="获取完整选项树")
async def list_options():
    """返回所有工艺及其关联的材料、后处理、交期选项"""
    processes = []
    for proc_id, mat_ids in config_service.PROCESS_MATERIALS.items():
        materials = []
        for mat_id in mat_ids:
            pricing = config_service.MATERIAL_PRICING.get(mat_id, {})
            mat_obj: dict = {
                "id": mat_id,
                "label": pricing.get("label", mat_id),
                "price": pricing.get("price", 0),
                "unit": pricing.get("unit", "g"),
            }
            if "category" in pricing:
                mat_obj["category"] = pricing["category"]
            if "image_url" in pricing:
                mat_obj["image_url"] = pricing["image_url"]
            if "description" in pricing:
                mat_obj["description"] = pricing["description"]
            materials.append(mat_obj)

        post_processes = []
        for pp_id in config_service.PROCESS_POST_PROCESS.get(proc_id, []):
            pp_config = config_service.POST_PROCESS_PRICING.get(pp_id, {})
            pp_obj: dict = {
                "id": pp_id,
                "label": pp_config.get("label", pp_id),
                "price_mode": pp_config.get("mode", "fixed"),
                "price_value": pp_config.get("value", 0),
            }
            if "description" in pp_config:
                pp_obj["description"] = pp_config["description"]
            post_processes.append(pp_obj)

        delivery_options = []
        for del_id, del_config in config_service.DELIVERY_SURCHARGE.items():
            delivery_options.append({
                "id": del_id,
                "label": del_config["label"],
                "surcharge": del_config["multiplier"] - 1.0,
                "days": del_config.get("days", 3),
            })

        processes.append({
            "id": proc_id,
            "label": PROCESS_LABELS.get(proc_id, proc_id),
            "materials": materials,
            "quality_options": QUALITY_OPTIONS.get(proc_id, QUALITY_OPTIONS["fdm"]),
            "post_processes": post_processes,
            "delivery_options": delivery_options,
        })

    return {
        "currency": "CNY",
        "time_cost_per_hour": config_service.TIME_COST_PER_HOUR,
        "markup_rate": config_service.BASE_MARKUP_RATE,
        "processes": processes,
    }

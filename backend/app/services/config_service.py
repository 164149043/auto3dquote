"""
配置缓存服务 — 从 SQLite 数据库读取定价配置，缓存到内存

暴露与 settings 完全相同形状的属性，消费者只需把 settings.X 换成 config_service.X。
"""

import json
from datetime import datetime

from app.db.database import SessionLocal
from app.core.config import settings
from app.db.models import (
    DeliveryOption,
    GlobalSetting,
    MachineVolumeLimit,
    Material,
    PostProcess,
    ProcessMaterial,
    ProcessPostProcess,
)
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)


class ConfigService:
    """从 DB 读取配置的缓存单例"""

    def __init__(self):
        self._material_pricing: dict[str, dict] = {}
        self._process_materials: dict[str, list[str]] = {}
        self._post_process_pricing: dict[str, dict] = {}
        self._process_post_process: dict[str, list[str]] = {}
        self._delivery_surcharge: dict[str, dict] = {}
        self._machine_volume_max_mm: dict[str, dict[str, float]] = {}
        self._global_settings: dict[str, object] = {}
        self._loaded = False

    def refresh(self) -> None:
        """从数据库重新加载全部缓存"""
        db = SessionLocal()
        try:
            self._load_materials(db)
            self._load_post_processes(db)
            self._load_delivery_options(db)
            self._load_machine_limits(db)
            self._load_global_settings(db)
            self._loaded = True
            logger.info("配置缓存已刷新")
        finally:
            db.close()

    # ==================== 属性（与 settings 同名同形状）====================

    @property
    def MATERIAL_PRICING(self) -> dict[str, dict]:
        self._ensure_loaded()
        return self._material_pricing

    @property
    def PROCESS_MATERIALS(self) -> dict[str, list[str]]:
        self._ensure_loaded()
        return self._process_materials

    @property
    def POST_PROCESS_PRICING(self) -> dict[str, dict]:
        self._ensure_loaded()
        return self._post_process_pricing

    @property
    def PROCESS_POST_PROCESS(self) -> dict[str, list[str]]:
        self._ensure_loaded()
        return self._process_post_process

    @property
    def DELIVERY_SURCHARGE(self) -> dict[str, dict]:
        self._ensure_loaded()
        return self._delivery_surcharge

    @property
    def MACHINE_VOLUME_MAX_MM(self) -> dict[str, dict[str, float]]:
        self._ensure_loaded()
        return self._machine_volume_max_mm

    @property
    def TIME_COST_PER_HOUR(self) -> float:
        return self._get_global("time_cost_per_hour", 35.0)

    @property
    def BASE_MARKUP_RATE(self) -> float:
        return self._get_global("base_markup_rate", 1.3)

    @property
    def CNC_SETUP_FEE(self) -> float:
        return self._get_global("cnc_setup_fee", 50.0)

    @property
    def CNC_MINIMUM_ORDER(self) -> float:
        return self._get_global("cnc_minimum_order", 100.0)

    @property
    def MINIMUM_ORDER_PER_PROCESS(self) -> dict[str, float]:
        default = settings.MINIMUM_ORDER_PER_PROCESS
        stored = self._get_global("minimum_order_per_process", None)
        return stored if stored else default

    @property
    def QUANTITY_DISCOUNT_TIERS(self) -> list[dict]:
        default = settings.QUANTITY_DISCOUNT_TIERS
        stored = self._get_global("quantity_discount_tiers", None)
        return stored if stored else default

    @property
    def DIFFICULTY_PRICING(self) -> dict:
        default = settings.DIFFICULTY_PRICING
        stored = self._get_global("difficulty_pricing", None)
        return stored if stored else default

    @property
    def SUPPORT_PRICING(self) -> dict:
        default = settings.SUPPORT_PRICING
        stored = self._get_global("support_pricing", None)
        return stored if stored else default

    @property
    def MATERIAL_COST_PER_GRAM(self) -> dict[str, float]:
        """向后兼容：从 MATERIAL_PRICING 提取 FDM 材料的 price"""
        return {
            k: v["price"]
            for k, v in self.MATERIAL_PRICING.items()
            if v.get("unit") == "g" and v.get("process") == "fdm"
        }

    # ==================== 内部方法 ====================

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.refresh()

    def _get_global(self, key: str, default) -> object:
        self._ensure_loaded()
        return self._global_settings.get(key, default)

    def _load_materials(self, db) -> None:
        pricing = {}
        for m in db.query(Material).all():
            d = {"price": m.price, "unit": m.unit, "density": m.density,
                 "process": m.process, "label": m.label}
            if m.machine_rate is not None:
                d["machine_rate"] = m.machine_rate
            if m.category is not None:
                d["category"] = m.category
            if m.image_url is not None:
                d["image_url"] = m.image_url
            if m.description is not None:
                d["description"] = m.description
            pricing[m.id] = d
        self._material_pricing = pricing

        proc_mats: dict[str, list[str]] = {}
        for pm in db.query(ProcessMaterial).order_by(ProcessMaterial.sort_order).all():
            proc_mats.setdefault(pm.process_id, []).append(pm.material_id)
        self._process_materials = proc_mats

    def _load_post_processes(self, db) -> None:
        pp_pricing = {}
        for pp in db.query(PostProcess).all():
            d = {"mode": pp.mode, "value": pp.value, "label": pp.label}
            if pp.description is not None:
                d["description"] = pp.description
            pp_pricing[pp.id] = d
        self._post_process_pricing = pp_pricing

        proc_pps: dict[str, list[str]] = {}
        for ppp in db.query(ProcessPostProcess).order_by(ProcessPostProcess.sort_order).all():
            proc_pps.setdefault(ppp.process_id, []).append(ppp.post_process_id)
        self._process_post_process = proc_pps

    def _load_delivery_options(self, db) -> None:
        surcharge = {}
        for d in db.query(DeliveryOption).order_by(DeliveryOption.sort_order).all():
            surcharge[d.id] = {"multiplier": d.multiplier, "days": d.days, "label": d.label}
        self._delivery_surcharge = surcharge

    def _load_machine_limits(self, db) -> None:
        limits = {}
        for m in db.query(MachineVolumeLimit).all():
            limits[m.process_id] = {"x": m.max_x, "y": m.max_y, "z": m.max_z}
        self._machine_volume_max_mm = limits

    def _load_global_settings(self, db) -> None:
        data = {}
        for gs in db.query(GlobalSetting).all():
            data[gs.key] = json.loads(gs.value)
        self._global_settings = data


# 全局单例
config_service = ConfigService()

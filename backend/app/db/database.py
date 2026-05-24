"""
数据库引擎、会话工厂、建表和种子数据
"""

import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.models import (
    Base,
    DeliveryOption,
    GlobalSetting,
    MachineVolumeLimit,
    Material,
    PostProcess,
    ProcessMaterial,
    ProcessPostProcess,
    QuoteRecord,
    User,
)
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)

# SQLite 文件路径
DB_PATH = Path(settings.TEMP_DIR).parent / "data" / "auto3dquote.db"
DB_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def get_db() -> Session:
    """FastAPI 依赖：返回一个 DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """建表（如果不存在），并处理增量迁移"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)

    # 增量迁移：为已有的 users 表添加 role 列
    _migrate_add_role_column()

    logger.info("数据库就绪: %s", DB_PATH)


def _migrate_add_role_column() -> None:
    """如果 users 表缺少 role 列，自动添加"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result]
            if "role" not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR DEFAULT 'user'"))
                conn.commit()
                logger.info("迁移: users 表新增 role 列")
    except Exception as e:
        logger.warning("迁移检查跳过: %s", e)


def seed_db() -> None:
    """如果表为空，从 config.py 默认值写入种子数据"""
    db = SessionLocal()
    try:
        _seed_materials(db)
        _seed_post_processes(db)
        _seed_delivery_options(db)
        _seed_machine_limits(db)
        _seed_global_settings(db)
        _seed_admin_user(db)
        db.commit()
        logger.info("种子数据检查完成")
    except Exception as e:
        db.rollback()
        logger.error("种子数据写入失败: %s", e)
        raise
    finally:
        db.close()


def _seed_materials(db: Session) -> None:
    if db.query(Material).first():
        return

    # category 映射: 按 material_id 分配分类
    _CATEGORY_MAP = {
        # 树脂
        "resin_standard": "resin", "resin_tough": "resin",
        "resin_high_temp": "resin", "resin_flexible": "resin",
        # 尼龙
        "PA12": "nylon", "PA11": "nylon", "PA12_GB": "nylon", "TPU_SLS": "nylon",
        # 金属
        "AL6061": "metal", "AL7075": "metal", "SS304": "metal",
        "SS316": "metal", "BRASS": "metal", "TC4": "metal",
    }

    now = datetime.now().isoformat()
    for mat_id, mat_data in settings.MATERIAL_PRICING.items():
        db.add(Material(
            id=mat_id,
            label=mat_data.get("label", mat_id),
            price=mat_data["price"],
            unit=mat_data["unit"],
            density=mat_data["density"],
            process=mat_data["process"],
            machine_rate=mat_data.get("machine_rate"),
            category=_CATEGORY_MAP.get(mat_id, "other"),
            image_url=mat_data.get("image_url"),
            description=mat_data.get("description"),
            sort_order=0,
            created_at=now,
            updated_at=now,
        ))

    for proc_id, mat_ids in settings.PROCESS_MATERIALS.items():
        for idx, mat_id in enumerate(mat_ids):
            db.add(ProcessMaterial(process_id=proc_id, material_id=mat_id, sort_order=idx))

    logger.info("种子: 写入 %d 条材料", db.query(Material).count())


def _seed_post_processes(db: Session) -> None:
    if db.query(PostProcess).first():
        return

    now = datetime.now().isoformat()
    for pp_id, pp_data in settings.POST_PROCESS_PRICING.items():
        db.add(PostProcess(
            id=pp_id,
            label=pp_data["label"],
            mode=pp_data["mode"],
            value=pp_data["value"],
            created_at=now,
            updated_at=now,
        ))

    for proc_id, pp_ids in settings.PROCESS_POST_PROCESS.items():
        for idx, pp_id in enumerate(pp_ids):
            db.add(ProcessPostProcess(process_id=proc_id, post_process_id=pp_id, sort_order=idx))

    logger.info("种子: 写入 %d 条后处理", db.query(PostProcess).count())


def _seed_delivery_options(db: Session) -> None:
    if db.query(DeliveryOption).first():
        return

    now = datetime.now().isoformat()
    for del_id, del_data in settings.DELIVERY_SURCHARGE.items():
        db.add(DeliveryOption(
            id=del_id,
            label=del_data["label"],
            multiplier=del_data["multiplier"],
            days=del_data["days"],
            sort_order=0,
            created_at=now,
            updated_at=now,
        ))

    logger.info("种子: 写入 %d 条交期选项", db.query(DeliveryOption).count())


def _seed_machine_limits(db: Session) -> None:
    if db.query(MachineVolumeLimit).first():
        return

    for proc_id, limits in settings.MACHINE_VOLUME_MAX_MM.items():
        db.add(MachineVolumeLimit(
            process_id=proc_id,
            max_x=limits["x"],
            max_y=limits["y"],
            max_z=limits["z"],
        ))

    logger.info("种子: 写入 %d 条设备限制", db.query(MachineVolumeLimit).count())


def _seed_global_settings(db: Session) -> None:
    if db.query(GlobalSetting).first():
        return

    now = datetime.now().isoformat()
    scalar_settings = {
        "time_cost_per_hour": {
            "value": json.dumps(settings.TIME_COST_PER_HOUR),
            "description": "机器时间费率 (¥/小时)",
        },
        "base_markup_rate": {
            "value": json.dumps(settings.BASE_MARKUP_RATE),
            "description": "基础加价率 (1.3 = 30% 利润)",
        },
        "cnc_setup_fee": {
            "value": json.dumps(settings.CNC_SETUP_FEE),
            "description": "CNC 装夹固定费 (¥)",
        },
        "cnc_minimum_order": {
            "value": json.dumps(settings.CNC_MINIMUM_ORDER),
            "description": "CNC 最低起订金额 (¥)",
        },
        "minimum_order_per_process": {
            "value": json.dumps(settings.MINIMUM_ORDER_PER_PROCESS),
            "description": "各工艺最低起订金额 (¥)",
        },
        "quantity_discount_tiers": {
            "value": json.dumps(settings.QUANTITY_DISCOUNT_TIERS),
            "description": "数量折扣阶梯配置",
        },
        "difficulty_pricing": {
            "value": json.dumps(settings.DIFFICULTY_PRICING),
            "description": "难度系数定价配置 (SA/V比 → 加价系数)",
        },
        "support_pricing": {
            "value": json.dumps(settings.SUPPORT_PRICING),
            "description": "支撑成本配置 (估算比例 × 单价)",
        },
    }

    for key, data in scalar_settings.items():
        db.add(GlobalSetting(
            key=key,
            value=data["value"],
            description=data["description"],
            updated_at=now,
        ))

    logger.info("种子: 写入 %d 条全局设置", db.query(GlobalSetting).count())


def _seed_admin_user(db: Session) -> None:
    """如果配置了管理员账号且不存在，自动创建"""
    if not settings.ADMIN_USERNAME or not settings.ADMIN_PASSWORD:
        return

    from app.core.security import hash_password

    existing = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
    if existing:
        if existing.role != "admin":
            existing.role = "admin"
            logger.info("种子: 更新用户 '%s' 为 admin 角色", settings.ADMIN_USERNAME)
        return

    now = datetime.now().isoformat()
    db.add(User(
        username=settings.ADMIN_USERNAME,
        hashed_password=hash_password(settings.ADMIN_PASSWORD),
        role="admin",
        is_active=1,
        created_at=now,
        updated_at=now,
    ))
    logger.info("种子: 创建管理员账号 '%s'", settings.ADMIN_USERNAME)

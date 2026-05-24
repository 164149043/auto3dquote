"""
SQLAlchemy ORM 模型 — 7 张配置表
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Material(Base):
    __tablename__ = "materials"

    id = Column(String, primary_key=True)
    label = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    unit = Column(String, nullable=False, default="g")
    density = Column(Float, nullable=False)
    process = Column(String, nullable=False)
    machine_rate = Column(Float, nullable=True)
    category = Column(String, nullable=True, default="other")
    image_url = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat())


class ProcessMaterial(Base):
    __tablename__ = "process_materials"

    process_id = Column(String, nullable=False)
    material_id = Column(String, ForeignKey("materials.id"), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)

    __table_args__ = (PrimaryKeyConstraint("process_id", "material_id"),)


class PostProcess(Base):
    __tablename__ = "post_processes"

    id = Column(String, primary_key=True)
    label = Column(String, nullable=False)
    mode = Column(String, nullable=False)  # "fixed" / "percentage"
    value = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat())


class ProcessPostProcess(Base):
    __tablename__ = "process_post_processes"

    process_id = Column(String, nullable=False)
    post_process_id = Column(String, ForeignKey("post_processes.id"), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)

    __table_args__ = (PrimaryKeyConstraint("process_id", "post_process_id"),)


class DeliveryOption(Base):
    __tablename__ = "delivery_options"

    id = Column(String, primary_key=True)
    label = Column(String, nullable=False)
    multiplier = Column(Float, nullable=False)
    days = Column(Integer, nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat())


class MachineVolumeLimit(Base):
    __tablename__ = "machine_volume_limits"

    process_id = Column(String, primary_key=True)
    max_x = Column(Float, nullable=False)
    max_y = Column(Float, nullable=False)
    max_z = Column(Float, nullable=False)


class GlobalSetting(Base):
    __tablename__ = "global_settings"

    key = Column(String, primary_key=True)
    value = Column(Text, nullable=False)  # JSON 字符串
    description = Column(Text, nullable=True)
    updated_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat())


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="user")  # "user" / "admin"
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat())


class QuoteRecord(Base):
    __tablename__ = "quote_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    process = Column(String(20), nullable=False)
    material = Column(String(50), nullable=False)
    quality = Column(String(20), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    delivery = Column(String(20), nullable=False)
    post_processing = Column(Text, nullable=True)
    status = Column(String(20), nullable=False)
    # 价格
    unit_price = Column(Float, nullable=False, default=0.0)
    total_price = Column(Float, nullable=False, default=0.0)
    material_cost = Column(Float, nullable=False, default=0.0)
    time_cost = Column(Float, nullable=False, default=0.0)
    post_process_cost = Column(Float, nullable=False, default=0.0)
    delivery_surcharge = Column(Float, nullable=False, default=0.0)
    difficulty_surcharge = Column(Float, nullable=False, default=0.0)
    support_cost = Column(Float, nullable=False, default=0.0)
    quantity_discount = Column(Float, nullable=False, default=0.0)
    # 模型数据
    volume_mm3 = Column(Float, nullable=False, default=0.0)
    surface_area_mm2 = Column(Float, nullable=False, default=0.0)
    bounding_box = Column(String(100), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    # 切片数据
    print_time_seconds = Column(Float, nullable=True)
    filament_used_grams = Column(Float, nullable=True)
    processing_time_seconds = Column(Float, nullable=False, default=0.0)
    created_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat())

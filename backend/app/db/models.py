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

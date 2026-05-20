"""
通用枚举和常量

定义工艺类型、材料类型、质量预设、后处理、交期、文件类型等枚举值。
"""

from enum import Enum


class ProcessType(str, Enum):
    """制造工艺类型"""
    FDM = "fdm"
    SLA = "sla"
    SLS = "sls"
    MJF = "mjf"
    CNC = "cnc"


class MaterialType(str, Enum):
    """材料类型（按工艺分组）"""
    # FDM
    PLA = "PLA"
    PETG = "PETG"
    ABS = "ABS"
    TPU = "TPU"
    NYLON = "NYLON"
    # SLA
    RESIN_STANDARD = "resin_standard"
    RESIN_TOUGH = "resin_tough"
    RESIN_HIGH_TEMP = "resin_high_temp"
    RESIN_FLEXIBLE = "resin_flexible"
    # SLS / MJF
    PA12 = "PA12"
    PA11 = "PA11"
    PA12_GB = "PA12_GB"
    TPU_SLS = "TPU_SLS"
    # CNC
    AL6061 = "AL6061"
    AL7075 = "AL7075"
    SS304 = "SS304"
    SS316 = "SS316"
    BRASS = "BRASS"
    TC4 = "TC4"


class QualityPreset(str, Enum):
    """打印质量预设"""
    DRAFT = "draft"        # 草稿质量: 0.3mm 层高
    STANDARD = "standard"  # 标准质量: 0.2mm 层高
    HIGH = "high"          # 高质量: 0.1mm 层高


class PostProcessType(str, Enum):
    """后处理选项"""
    # 通用
    SANDING = "sanding"
    PAINTING = "painting"
    POLISHING = "polishing"
    # CNC 专用
    TAPPING = "tapping"
    HEAT_TREATMENT = "heat_treatment"
    ANODIZING = "anodizing"
    ELECTROPLATING = "electroplating"
    # 3D 打印专用
    SUPPORT_REMOVAL = "support_removal"
    UV_CURING = "uv_curing"
    INFILTRATION = "infiltration"
    DYEING = "dyeing"               # 染色（SLS/MJF）


class DeliveryOption(str, Enum):
    """交期选项"""
    STANDARD = "standard"   # 3 天
    EXPRESS = "express"     # 2 天
    URGENT = "urgent"       # 1 天


class FileType(str, Enum):
    """支持的 3D 模型文件类型"""
    STL = "stl"
    OBJ = "obj"
    THREE_MF = "3mf"
    STP = "stp"
    STEP = "step"

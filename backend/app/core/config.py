"""
全局配置模块

使用 pydantic-settings 从环境变量和 .env 文件加载配置。
所有配置项都有合理的默认值，可通过 .env 覆盖。
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用全局配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ==================== PrusaSlicer 配置 ====================
    # PrusaSlicer CLI 可执行文件路径 (Windows 使用 prusa-slicer-console.exe)
    PRUSA_SLICER_PATH: str = r"D:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer-console.exe"
    # 切片超时时间 (秒)，复杂模型可能需要更长时间
    PRUSA_SLICER_TIMEOUT: int = 300
    # 切片配置文件目录
    PRUSA_PROFILES_DIR: str = str(Path(__file__).parent.parent.parent / "slicer_profiles")

    # ==================== 文件上传配置 ====================
    # 最大文件大小 (MB)
    MAX_FILE_SIZE_MB: int = 100
    # 允许的文件扩展名
    ALLOWED_EXTENSIONS: list[str] = [
        ".stl", ".STL", ".obj", ".OBJ", ".3mf", ".3MF",
        ".stp", ".STP", ".step", ".STEP",
    ]

    # ==================== 临时文件配置 ====================
    # 临时文件存储目录
    TEMP_DIR: str = str(Path(__file__).parent.parent.parent / "tmp")
    # 残留文件清理阈值 (秒)，启动时删除超过此时间的临时文件
    TEMP_FILE_MAX_AGE_SECONDS: int = 3600

    # ==================== 报价配置 (币种: CNY/¥) ====================
    # FDM 材料单价 (¥/克) — 向后兼容
    MATERIAL_COST_PER_GRAM: dict[str, float] = {
        "PLA": 0.18,
        "PETG": 0.25,
        "ABS": 0.22,
        "TPU": 0.32,
        "NYLON": 0.45,
    }
    # 机器时间费率 (¥/小时)
    TIME_COST_PER_HOUR: float = 35.0
    # 基础加价率 (1.3 = 30% 利润)
    BASE_MARKUP_RATE: float = 1.3

    # ==================== 工艺-材料映射 ====================
    PROCESS_MATERIALS: dict[str, list[str]] = {
        "fdm": ["PLA", "PETG", "ABS", "TPU", "NYLON"],
        "sla": ["resin_standard", "resin_tough", "resin_high_temp", "resin_flexible"],
        "sls": ["PA12", "PA11", "PA12_GB", "TPU_SLS"],
        "mjf": ["PA12", "PA11"],
        "cnc": ["AL6061", "AL7075", "SS304", "SS316", "BRASS", "TC4"],
    }

    # ==================== 材料定价表 ====================
    # price: 单价; unit: 计价单位; density: 密度 g/cm³; process: 所属工艺
    MATERIAL_PRICING: dict[str, dict] = {
        # FDM（按重量 ¥/g）
        "PLA":   {"price": 0.18, "unit": "g",  "density": 1.24, "process": "fdm", "label": "PLA",
                  "description": "聚乳酸，最常见的3D打印材料。环保可降解，打印温度低，成型效果好，表面光滑。适合原型制作、展示模型和日常用品。强度一般，不耐高温（60°C以上易变形）。"},
        "PETG":  {"price": 0.25, "unit": "g",  "density": 1.27, "process": "fdm", "label": "PETG",
                  "description": "聚对苯二甲酸乙二醇酯改性版，兼具PLA的易打印性和ABS的韧性。耐化学腐蚀，防水性好，韧性高，不易脆裂。适合功能件、外壳、容器等需要耐用性的场景。"},
        "ABS":   {"price": 0.22, "unit": "g",  "density": 1.04, "process": "fdm", "label": "ABS",
                  "description": "丙烯腈-丁二烯-苯乙烯共聚物，工业级工程塑料。耐冲击、耐高温，可用丙酮抛光使表面光滑。适合汽车零件、电子外壳等功能性零件。打印时需要加热平台和封闭腔体。"},
        "TPU":   {"price": 0.32, "unit": "g",  "density": 1.21, "process": "fdm", "label": "TPU",
                  "description": "热塑性聚氨酯弹性体，柔性材料。具有优异的弹性和耐磨性，可反复弯曲不断裂。适合手机壳、密封圈、减震垫、穿戴设备等需要柔韧性的应用。"},
        "NYLON": {"price": 0.45, "unit": "g",  "density": 1.14, "process": "fdm", "label": "NYLON",
                  "description": "尼龙（聚酰胺），高强度工程塑料。耐磨性极佳，韧性好，耐疲劳，自润滑。适合齿轮、轴承、卡扣等受力零件。吸湿性强，打印前需干燥处理。"},
        # SLA（按体积 ¥/cm³）
        "resin_standard":   {"price": 0.50, "unit": "cm3", "density": 1.10, "process": "sla", "label": "标准树脂",
                             "description": "标准光敏树脂，SLA光固化打印最常用的材料。表面细腻光滑，精度极高（可达0.025mm层厚），细节还原度好。适合珠宝原型、精密零件、展示模型。"},
        "resin_tough":      {"price": 0.80, "unit": "cm3", "density": 1.15, "process": "sla", "label": "韧性树脂",
                             "description": "韧性树脂，在标准树脂基础上提高了抗冲击性和柔韧性。不易脆裂，可承受一定弯折。适合功能原型、卡扣零件、需要受力的结构件。"},
        "resin_high_temp":  {"price": 1.00, "unit": "cm3", "density": 1.12, "process": "sla", "label": "耐高温树脂",
                             "description": "耐高温树脂，热变形温度可达200°C以上。在高温环境下保持形状稳定，力学性能优异。适合注塑模具、热端零件、发动机周边件等高温场景。"},
        "resin_flexible":   {"price": 0.65, "unit": "cm3", "density": 1.08, "process": "sla", "label": "柔性树脂",
                             "description": "柔性光敏树脂，固化后具有橡胶般的弹性。邵氏硬度约60A-80A，可反复弯折压缩。适合密封件、缓冲垫、柔性接头、穿戴设备等。"},
        # SLS（按重量 ¥/g）
        "PA12":    {"price": 0.55, "unit": "g",  "density": 1.01, "process": "sls", "label": "PA12 尼龙",
                   "description": "PA12尼龙粉末，SLS激光烧结最常用的材料。密度低、韧性好、耐化学腐蚀，力学性能均衡。适合复杂几何结构的零件，无需支撑即可打印。广泛用于功能件和小批量生产。"},
        "PA11":    {"price": 0.65, "unit": "g",  "density": 1.03, "process": "sls", "label": "PA11 尼龙",
                   "description": "PA11尼龙粉末，由蓖麻油提取的生物基材料。比PA12更柔韧，耐冲击性更好，耐疲劳性能优异。适合卡扣、铰链、运动器材等需要反复变形的零件。"},
        "PA12_GB": {"price": 0.70, "unit": "g",  "density": 1.20, "process": "sls", "label": "PA12+玻珠",
                   "description": "PA12+玻璃珠复合粉末，在PA12基础上添加玻璃微珠。刚性和尺寸稳定性显著提升，热变形温度更高。适合需要精密配合的功能零件、夹具和工装。"},
        "TPU_SLS": {"price": 0.85, "unit": "g",  "density": 1.10, "process": "sls", "label": "TPU 粉末",
                   "description": "TPU粉末材料，SLS工艺直接烧结成型弹性体。邵氏硬度约85A，弹性回复率好，耐磨损。适合密封圈、减震垫、运动鞋底、柔性管道等。"},
        # CNC（按重量 ¥/kg）
        "AL6061": {"price": 35,  "unit": "kg", "density": 2.70, "process": "cnc", "label": "铝合金6061", "machine_rate": 80,
                   "description": "6061铝合金，最通用的铝合金材料。具有良好的成型性、可焊性和耐腐蚀性，强度适中。广泛用于结构件、支架、外壳、散热器等。CNC加工性能优异，表面可阳极氧化。"},
        "AL7075": {"price": 55,  "unit": "kg", "density": 2.81, "process": "cnc", "label": "铝合金7075", "machine_rate": 100,
                   "description": "7075超硬铝合金，强度最高的铝合金之一（又称航空铝）。抗拉强度可达572MPa，重量轻。适合高强度结构件、无人机机架、运动器材。加工难度较高，不可焊接。"},
        "SS304":  {"price": 28,  "unit": "kg", "density": 7.93, "process": "cnc", "label": "不锈钢304",  "machine_rate": 90,
                   "description": "304不锈钢，应用最广泛的不锈钢。耐腐蚀性好，成型性佳，表面美观。适合食品级容器、化工设备、医疗器械、建筑装饰等。CNC加工需注意加工硬化。"},
        "SS316":  {"price": 45,  "unit": "kg", "density": 7.98, "process": "cnc", "label": "不锈钢316",  "machine_rate": 100,
                   "description": "316不锈钢，在304基础上添加钼元素，耐腐蚀性更强。特别耐氯离子腐蚀（海洋环境）。适合医疗器械、化工管道、船舶配件等高腐蚀环境应用。"},
        "BRASS":  {"price": 50,  "unit": "kg", "density": 8.50, "process": "cnc", "label": "黄铜",        "machine_rate": 85,
                   "description": "黄铜（铜锌合金），金黄色外观，导电导热性好。耐腐蚀，抗菌，可抛光至镜面效果。适合电气连接件、阀门、装饰件、乐器配件。加工性能优异。"},
        "TC4":    {"price": 280, "unit": "kg", "density": 4.51, "process": "cnc", "label": "钛合金TC4",   "machine_rate": 150,
                   "description": "TC4钛合金（Ti-6Al-4V），高强度轻质合金。比强度高，耐腐蚀性极佳，生物相容性好。密度仅4.51g/cm³但强度与钢相当。航空航天、医疗器械、高端运动器材首选材料。"},
    }

    # ==================== 后处理定价 ====================
    POST_PROCESS_PRICING: dict[str, dict] = {
        "sanding":         {"mode": "percentage", "value": 0.15, "label": "打磨"},
        "painting":        {"mode": "percentage", "value": 0.20, "label": "喷漆"},
        "polishing":       {"mode": "percentage", "value": 0.20, "label": "抛光"},
        "tapping":         {"mode": "fixed",      "value": 5.0,  "label": "攻丝/攻牙"},
        "heat_treatment":  {"mode": "fixed",      "value": 50.0, "label": "热处理"},
        "anodizing":       {"mode": "percentage", "value": 0.25, "label": "阳极氧化"},
        "electroplating":  {"mode": "percentage", "value": 0.30, "label": "电镀"},
        "support_removal": {"mode": "percentage", "value": 0.08, "label": "支撑拆除"},
        "uv_curing":       {"mode": "fixed",      "value": 8.0,  "label": "UV后固化"},
        "infiltration":    {"mode": "fixed",      "value": 20.0, "label": "渗透强化"},
        "dyeing":          {"mode": "fixed",      "value": 12.0, "label": "染色"},
    }

    # 工艺 → 可用后处理映射
    PROCESS_POST_PROCESS: dict[str, list[str]] = {
        "fdm": ["sanding", "painting", "polishing", "support_removal"],
        "sla": ["sanding", "painting", "uv_curing", "support_removal"],
        "sls": ["sanding", "painting", "polishing", "infiltration"],
        "mjf": ["sanding", "painting", "polishing", "dyeing"],
        "cnc": ["tapping", "heat_treatment", "anodizing", "electroplating", "polishing"],
    }

    # ==================== 交期加价 ====================
    DELIVERY_SURCHARGE: dict[str, dict] = {
        "standard": {"multiplier": 1.0,  "days": 3, "label": "标准 (3天)"},
        "express":  {"multiplier": 1.15, "days": 2, "label": "加急 (2天)"},
        "urgent":   {"multiplier": 1.35, "days": 1, "label": "特急 (1天)"},
    }

    # ==================== CNC 专用配置 ====================
    CNC_SETUP_FEE: float = 50.0
    CNC_MINIMUM_ORDER: float = 100.0

    # ==================== 最低起订价 ====================
    MINIMUM_ORDER_PER_PROCESS: dict[str, float] = {
        "fdm": 30.0,
        "sla": 30.0,
        "sls": 30.0,
        "mjf": 30.0,
        "cnc": 100.0,
    }

    # ==================== 数量折扣阶梯 ====================
    QUANTITY_DISCOUNT_TIERS: list[dict] = [
        {"min_qty": 1,  "discount": 0.00, "label": "1+件"},
        {"min_qty": 5,  "discount": 0.03, "label": "5+件 (-3%)"},
        {"min_qty": 10, "discount": 0.06, "label": "10+件 (-6%)"},
        {"min_qty": 20, "discount": 0.09, "label": "20+件 (-9%)"},
        {"min_qty": 50, "discount": 0.12, "label": "50+件 (-12%)"},
    ]

    # ==================== 打印机/设备配置 ====================
    # 各工艺的构建体积上限 (mm)，超过此尺寸的模型会报错
    MACHINE_VOLUME_MAX_MM: dict[str, dict[str, float]] = {
        "fdm":  {"x": 350, "y": 350, "z": 400},
        "sla":  {"x": 300, "y": 300, "z": 300},
        "sls":  {"x": 400, "y": 400, "z": 450},
        "mjf":  {"x": 400, "y": 300, "z": 400},
        "cnc":  {"x": 1200, "y": 800, "z": 600},
    }

    # ==================== 日志配置 ====================
    LOG_LEVEL: str = "INFO"

    # ==================== 管理后台配置 ====================
    # Admin API 认证 Token，留空则启动时自动生成并打印到日志
    ADMIN_TOKEN: str = ""


# 全局配置单例
settings = Settings()

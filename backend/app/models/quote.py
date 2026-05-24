"""
报价响应模型

包含完整的成本分解和最终报价。
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.analysis import MeshAnalysisResult
from app.models.slicing import SlicingResult


class MaterialCost(BaseModel):
    """材料成本明细"""
    material_type: str = Field(..., description="材料类型")
    unit_price: float = Field(..., description="单价")
    quantity: float = Field(..., description="用量（克/cm³/kg，与单价匹配）")
    unit: str = Field("g", description="计价单位: g / cm3 / kg")
    subtotal: float = Field(..., description="材料小计 (¥)")


class TimeCost(BaseModel):
    """时间成本明细"""
    rate_per_hour: float = Field(..., description="时费率 (¥/小时)")
    hours: float = Field(..., description="打印时长 (小时)")
    subtotal: float = Field(..., description="时间小计 (¥)")


class PostProcessCost(BaseModel):
    """后处理费用明细"""
    name: str = Field(..., description="后处理名称")
    type: str = Field(..., description="后处理类型")
    unit_price: float = Field(..., description="单价 (¥)")
    subtotal: float = Field(..., description="小计 (¥)")


class CostBreakdown(BaseModel):
    """完整成本分解"""
    material_cost: MaterialCost = Field(..., description="材料成本")
    time_cost: TimeCost = Field(..., description="时间成本")
    post_process_costs: list[PostProcessCost] = Field(default_factory=list, description="后处理费用")
    delivery_surcharge: float = Field(0.0, description="交期加急费 (¥)")
    difficulty_score: float = Field(0.0, description="难度评分 (0.0~1.0)")
    difficulty_multiplier: float = Field(1.0, description="难度系数 (1.0=无加价, 1.3=加价30%)")
    difficulty_surcharge: float = Field(0.0, description="难度加价金额 (¥)")
    support_weight: float = Field(0.0, description="支撑材料重量 (g)")
    support_cost: float = Field(0.0, description="支撑材料成本 (¥)")
    quantity_discount: float = Field(0.0, description="数量折扣金额 (¥)")
    quantity_discount_rate: float = Field(0.0, description="数量折扣率 (如 0.06 = 6%)")
    base_price: float = Field(..., description="基础价格 (材料+时间+后处理+交期)")
    markup_rate: float = Field(..., description="加价率")
    unit_price: float = Field(..., description="单价 (加价后)")
    quantity: int = Field(..., description="数量")
    total_price: float = Field(..., description="总价")


class QuoteResponse(BaseModel):
    """报价 API 完整响应"""
    status: str = Field("success", description="状态: success / warning / partial")
    analysis: MeshAnalysisResult = Field(..., description="网格分析结果")
    slicing: SlicingResult | None = Field(None, description="切片结果 (降级模式可能为 null)")
    quote: CostBreakdown | None = Field(None, description="报价明细 (降级模式可能为 null)")
    warnings: list[str] = Field(default_factory=list, description="所有警告")
    processing_time_seconds: float = Field(0.0, description="总处理耗时 (秒)")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="时间戳")


class QuoteRecordItem(BaseModel):
    """报价记录列表摘要"""
    id: int
    filename: str
    process: str
    material: str
    quantity: int
    status: str
    unit_price: float
    total_price: float
    created_at: str


class QuoteRecordDetail(QuoteRecordItem):
    """报价记录完整详情"""
    quality: str
    delivery: str
    post_processing: str | None
    material_cost: float
    time_cost: float
    post_process_cost: float
    delivery_surcharge: float
    difficulty_surcharge: float
    support_cost: float
    quantity_discount: float
    volume_mm3: float
    surface_area_mm2: float
    bounding_box: str | None
    file_size_bytes: int | None
    print_time_seconds: float | None
    filament_used_grams: float | None
    processing_time_seconds: float


class QuoteRecordListResponse(BaseModel):
    """报价记录分页响应"""
    total: int
    page: int
    page_size: int
    records: list[QuoteRecordItem]

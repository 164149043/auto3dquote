"""
报价计算引擎

根据切片结果 (耗材重量、打印时间) 计算报价。

公式:
  material_cost = filament_used_grams × cost_per_gram[material]
  time_cost = (print_time_seconds / 3600) × rate_per_hour
  base_price = material_cost + time_cost
  unit_price = base_price × markup_rate
  total_price = unit_price × quantity
"""

from app.core.config import settings
from app.models.quote import CostBreakdown, MaterialCost, TimeCost
from app.models.slicing import SlicingResult
from app.utils.math_utils import round_price


class QuoteEngine:
    """报价计算引擎"""

    def __init__(self):
        self.material_costs = settings.MATERIAL_COST_PER_GRAM
        self.time_rate = settings.TIME_COST_PER_HOUR
        self.markup_rate = settings.BASE_MARKUP_RATE

    def calculate(
        self,
        slicing_result: SlicingResult,
        material: str,
        quantity: int = 1,
    ) -> CostBreakdown:
        """
        根据切片结果和材料类型计算完整报价。

        返回: CostBreakdown 包含完整的成本分解
        """
        # 材料成本
        cost_per_gram = self.material_costs.get(material, 0.18)
        weight_grams = slicing_result.filament_used_grams
        material_subtotal = round_price(weight_grams * cost_per_gram)

        material_cost = MaterialCost(
            material_type=material,
            unit_price=cost_per_gram,
            quantity=weight_grams,
            unit="g",
            subtotal=material_subtotal,
        )

        # 时间成本
        hours = slicing_result.print_time_seconds / 3600.0
        time_subtotal = round_price(hours * self.time_rate)

        time_cost = TimeCost(
            rate_per_hour=self.time_rate,
            hours=round(hours, 2),
            subtotal=time_subtotal,
        )

        # 汇总
        base_price = round_price(material_subtotal + time_subtotal)
        unit_price = round_price(base_price * self.markup_rate)
        total_price = round_price(unit_price * quantity)

        return CostBreakdown(
            material_cost=material_cost,
            time_cost=time_cost,
            base_price=base_price,
            markup_rate=self.markup_rate,
            unit_price=unit_price,
            quantity=quantity,
            total_price=total_price,
            quantity_discount=0.0,
            quantity_discount_rate=0.0,
            difficulty_score=0.0,
            difficulty_multiplier=1.0,
            difficulty_surcharge=0.0,
        )

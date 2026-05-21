"""
CNC 报价策略

CNC 按毛坯材料 + 加工时长计费：
  stock_cost = bounding_box_volume_cm3 × density / 1000 × price_per_kg
  machining_cost = estimated_hours × machine_rate_per_hour
  setup_fee = 固定装夹费
  后处理和交期费用叠加
"""

from app.services.config_service import config_service
from app.models.analysis import MeshAnalysisResult
from app.models.common import DeliveryOption, PostProcessType
from app.models.quote import CostBreakdown, MaterialCost, TimeCost
from app.models.slicing import SlicingResult
from app.services.pricing.base import PricingStrategy
from app.services.pricing.utils import (
    calc_post_process_costs,
    calc_delivery_surcharge,
    calc_difficulty_multiplier,
    calc_quantity_discount,
    apply_minimum_order,
)
from app.utils.math_utils import round_price


class CNCPricingStrategy(PricingStrategy):
    """CNC 数控加工报价策略"""

    def calculate(
        self,
        analysis: MeshAnalysisResult,
        slicing: SlicingResult | None,
        material: str,
        quantity: int = 1,
        post_processing: list[PostProcessType] | None = None,
        delivery: DeliveryOption = DeliveryOption.STANDARD,
    ) -> CostBreakdown:
        pricing = config_service.MATERIAL_PRICING.get(material, {})
        density = pricing.get("density", 2.70)
        price_per_kg = pricing.get("price", 35)
        machine_rate = pricing.get("machine_rate", 80)

        # 毛坯体积 = 包围盒尺寸 × 1.1 (留加工余量 10%)
        bbox = analysis.bounding_box
        stock_volume_cm3 = (bbox.x_mm * bbox.y_mm * bbox.z_mm) / 1000.0 * 1.1
        stock_weight_kg = stock_volume_cm3 * density / 1000.0
        stock_cost = round_price(stock_weight_kg * price_per_kg)

        material_cost = MaterialCost(
            material_type=material,
            unit_price=price_per_kg,
            quantity=round(stock_weight_kg, 4),
            unit="kg",
            subtotal=stock_cost,
        )

        # 加工时长估算：基于体积和表面积的经验公式
        volume_cm3 = analysis.volume_mm3 / 1000.0
        surface_cm2 = analysis.surface_area_mm2 / 100.0
        # 体积去除率 + 表面精加工时间
        estimated_hours = (volume_cm3 * 0.02 + surface_cm2 * 0.005) + 0.5  # 最少 0.5h
        machining_cost = round_price(estimated_hours * machine_rate)
        setup_fee = config_service.CNC_SETUP_FEE

        time_cost = TimeCost(
            rate_per_hour=machine_rate,
            hours=round(estimated_hours, 2),
            subtotal=machining_cost,
        )

        base_before_extras = stock_cost + machining_cost + setup_fee
        pp_costs = calc_post_process_costs(post_processing, base_before_extras)
        delivery_fee = calc_delivery_surcharge(delivery, base_before_extras, time_cost=machining_cost)

        difficulty_multiplier, difficulty_score = calc_difficulty_multiplier(
            analysis.surface_area_mm2, analysis.volume_mm3,
            override_coefficient=config_service.DIFFICULTY_PRICING.get("cnc_coefficient", 0.10),
        )
        pre_difficulty = base_before_extras + pp_costs["total"] + delivery_fee
        difficulty_surcharge = round_price(pre_difficulty * (difficulty_multiplier - 1.0))

        base_price = round_price(pre_difficulty + difficulty_surcharge)
        unit_price_before_discount = round_price(base_price * config_service.BASE_MARKUP_RATE)

        discount_amount, discount_rate = calc_quantity_discount(quantity, unit_price_before_discount)
        unit_price = round_price(unit_price_before_discount - discount_amount)

        unit_price, effective_markup = apply_minimum_order("cnc", unit_price, base_price)
        total_price = round_price(unit_price * quantity)

        return CostBreakdown(
            material_cost=material_cost,
            time_cost=time_cost,
            post_process_costs=pp_costs["items"],
            delivery_surcharge=round_price(delivery_fee),
            difficulty_score=difficulty_score,
            difficulty_multiplier=difficulty_multiplier,
            difficulty_surcharge=difficulty_surcharge,
            quantity_discount=discount_amount,
            quantity_discount_rate=discount_rate,
            base_price=base_price,
            markup_rate=effective_markup,
            unit_price=unit_price,
            quantity=quantity,
            total_price=total_price,
        )

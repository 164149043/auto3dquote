"""
FDM 报价策略

优先使用切片数据（精确），切片不可用时基于网格分析估算（降级）：
  material_cost = filament_used_grams × cost_per_gram
  time_cost = hours × rate_per_hour
  后处理和交期费用叠加
  unit_price = (material + time + post_process + delivery) × markup - quantity_discount
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
    calc_support_cost,
    calc_quantity_discount,
    apply_minimum_order,
)
from app.utils.math_utils import round_price


class FDMPricingStrategy(PricingStrategy):
    """FDM 3D 打印报价策略"""

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
        cost_per_gram = pricing.get("price", config_service.MATERIAL_COST_PER_GRAM.get(material, 0.18))
        density = pricing.get("density", 1.24)

        if slicing is not None:
            # 精确模式：使用切片结果
            weight_grams = slicing.filament_used_grams
            hours = slicing.print_time_seconds / 3600.0
        else:
            # 降级模式：基于网格分析估算
            # 重量 = 模型体积 × 密度 × 1.2（考虑填充和支撑）
            weight_grams = round(analysis.volume_mm3 / 1000.0 * density * 1.2, 1)
            # 时间 = 基于典型 FDM 吞吐量 (~40cm³/h + 20% 开销)
            volume_cm3 = analysis.volume_mm3 / 1000.0
            hours = round((volume_cm3 / 40.0) * 1.2, 2)
            hours = max(hours, 0.5)  # 最低 0.5 小时

        material_subtotal = round_price(weight_grams * cost_per_gram)
        time_subtotal = round_price(hours * config_service.TIME_COST_PER_HOUR)

        material_cost = MaterialCost(
            material_type=material,
            unit_price=cost_per_gram,
            quantity=weight_grams,
            unit="g",
            subtotal=material_subtotal,
        )

        time_cost = TimeCost(
            rate_per_hour=config_service.TIME_COST_PER_HOUR,
            hours=round(hours, 2),
            subtotal=time_subtotal,
        )

        pp_costs = calc_post_process_costs(post_processing, material_subtotal + time_subtotal)
        delivery_fee = calc_delivery_surcharge(delivery, material_subtotal + time_subtotal, time_cost=time_subtotal)

        difficulty_multiplier, difficulty_score = calc_difficulty_multiplier(
            analysis.surface_area_mm2, analysis.volume_mm3,
        )

        support_weight, support_cost_val, support_price_per_gram = calc_support_cost(
            model_weight_g=weight_grams,
            model_height_mm=analysis.bounding_box.z_mm,
            difficulty_score=difficulty_score,
            material_price_per_gram=cost_per_gram,
        )

        pre_difficulty = material_subtotal + support_cost_val + time_subtotal + pp_costs["total"] + delivery_fee
        difficulty_surcharge = round_price(pre_difficulty * (difficulty_multiplier - 1.0))

        base_price = round_price(pre_difficulty + difficulty_surcharge)
        unit_price_before_discount = round_price(base_price * config_service.BASE_MARKUP_RATE)

        discount_amount, discount_rate = calc_quantity_discount(quantity, unit_price_before_discount)
        unit_price = round_price(unit_price_before_discount - discount_amount)

        unit_price, effective_markup = apply_minimum_order("fdm", unit_price, base_price)
        total_price = round_price(unit_price * quantity)

        return CostBreakdown(
            material_cost=material_cost,
            time_cost=time_cost,
            post_process_costs=pp_costs["items"],
            delivery_surcharge=round_price(delivery_fee),
            difficulty_score=difficulty_score,
            difficulty_multiplier=difficulty_multiplier,
            difficulty_surcharge=difficulty_surcharge,
            support_weight=support_weight,
            support_cost=support_cost_val,
            quantity_discount=discount_amount,
            quantity_discount_rate=discount_rate,
            base_price=base_price,
            markup_rate=effective_markup,
            unit_price=unit_price,
            quantity=quantity,
            total_price=total_price,
        )

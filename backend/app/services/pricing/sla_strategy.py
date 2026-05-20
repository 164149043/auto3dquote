"""
SLA / SLS / MJF 报价策略

SLA 按树脂体积计费（¥/cm³），SLS/MJF 按粉末重量计费（¥/g）。
通过 MATERIAL_PRICING 中的 unit 字段自动区分计价方式。
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
    calc_quantity_discount,
    apply_minimum_order,
)
from app.utils.math_utils import round_price


class SLAPricingStrategy(PricingStrategy):
    """SLA/SLS/MJF 报价策略（根据材料 unit 字段区分按体积还是按重量计费）"""

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
        price = pricing.get("price", 0.50)
        density = pricing.get("density", 1.10)
        unit = pricing.get("unit", "cm3")

        volume_cm3 = analysis.volume_mm3 / 1000.0

        if unit == "g":
            # SLS/MJF：按重量计费
            weight_grams = round(volume_cm3 * density, 2)
            material_subtotal = round_price(weight_grams * price)
            material_cost = MaterialCost(
                material_type=material,
                unit_price=price,
                quantity=weight_grams,
                unit="g",
                subtotal=material_subtotal,
            )
        else:
            # SLA：按体积计费
            material_subtotal = round_price(volume_cm3 * price)
            material_cost = MaterialCost(
                material_type=material,
                unit_price=price,
                quantity=round(volume_cm3, 2),
                unit="cm3",
                subtotal=material_subtotal,
            )

        # 时间估算
        if slicing:
            hours = slicing.print_time_seconds / 3600.0
        else:
            layer_height_mm = 0.05
            estimated_layers = analysis.bounding_box.z_mm / layer_height_mm
            hours = estimated_layers * 8.0 / 3600.0
            hours = max(hours, 0.5)  # 最低 0.5 小时

        time_subtotal = round_price(hours * config_service.TIME_COST_PER_HOUR)

        time_cost = TimeCost(
            rate_per_hour=config_service.TIME_COST_PER_HOUR,
            hours=round(hours, 2),
            subtotal=time_subtotal,
        )

        pp_costs = calc_post_process_costs(post_processing, material_subtotal + time_subtotal)
        delivery_fee = calc_delivery_surcharge(delivery, material_subtotal + time_subtotal, time_cost=time_subtotal)

        base_price = round_price(material_subtotal + time_subtotal + pp_costs["total"] + delivery_fee)
        unit_price_before_discount = round_price(base_price * config_service.BASE_MARKUP_RATE)

        discount_amount, discount_rate = calc_quantity_discount(quantity, unit_price_before_discount)
        unit_price = round_price(unit_price_before_discount - discount_amount)

        unit_price, effective_markup = apply_minimum_order("sla", unit_price, base_price)
        total_price = round_price(unit_price * quantity)

        return CostBreakdown(
            material_cost=material_cost,
            time_cost=time_cost,
            post_process_costs=pp_costs["items"],
            delivery_surcharge=round_price(delivery_fee),
            quantity_discount=discount_amount,
            quantity_discount_rate=discount_rate,
            base_price=base_price,
            markup_rate=effective_markup,
            unit_price=unit_price,
            quantity=quantity,
            total_price=total_price,
        )

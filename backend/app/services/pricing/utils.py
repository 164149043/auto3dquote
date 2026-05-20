"""
报价策略共享工具函数

后处理费用、交期费用、数量折扣、最低起订价的计算逻辑，被所有策略共用。
"""

from app.services.config_service import config_service
from app.models.common import DeliveryOption, PostProcessType
from app.models.quote import PostProcessCost
from app.utils.math_utils import round_price


def calc_post_process_costs(
    post_processing: list[PostProcessType] | None,
    base_amount: float,
) -> dict:
    """
    计算后处理费用。

    返回: {"items": [...], "total": float}
    """
    if not post_processing:
        return {"items": [], "total": 0.0}

    items: list[PostProcessCost] = []
    total = 0.0

    for pp in post_processing:
        config = config_service.POST_PROCESS_PRICING.get(pp.value)
        if not config:
            continue

        if config["mode"] == "fixed":
            subtotal = config["value"]
        elif config["mode"] == "percentage":
            subtotal = base_amount * config["value"]
        else:
            continue

        subtotal = round_price(subtotal)
        total += subtotal

        items.append(PostProcessCost(
            name=config["label"],
            type=pp.value,
            unit_price=config["value"],
            subtotal=subtotal,
        ))

    return {"items": items, "total": round_price(total)}


def calc_delivery_surcharge(
    delivery: DeliveryOption,
    base_amount: float,
    time_cost: float | None = None,
) -> float:
    """计算交期加急费用。仅对时间成本部分加价。"""
    config = config_service.DELIVERY_SURCHARGE.get(delivery.value, config_service.DELIVERY_SURCHARGE["standard"])
    multiplier = config["multiplier"]
    if multiplier <= 1.0:
        return 0.0
    effective_base = time_cost if time_cost is not None else base_amount
    return effective_base * (multiplier - 1.0)


def calc_quantity_discount(
    quantity: int,
    unit_price_before_discount: float,
) -> tuple[float, float]:
    """
    计算数量折扣。
    返回: (discount_amount, discount_rate)
    """
    tiers = config_service.QUANTITY_DISCOUNT_TIERS
    applicable_rate = 0.0
    for tier in sorted(tiers, key=lambda t: t["min_qty"]):
        if quantity >= tier["min_qty"]:
            applicable_rate = tier["discount"]
    if applicable_rate <= 0.0:
        return 0.0, 0.0
    discount_amount = round_price(unit_price_before_discount * applicable_rate)
    return discount_amount, applicable_rate


def apply_minimum_order(
    process: str,
    unit_price: float,
    base_price: float,
) -> tuple[float, float]:
    """
    应用最低起订价。
    返回: (adjusted_unit_price, effective_markup_rate)
    """
    minimums = config_service.MINIMUM_ORDER_PER_PROCESS
    minimum = minimums.get(process, 0.0)
    if minimum <= 0.0 or unit_price >= minimum:
        return unit_price, config_service.BASE_MARKUP_RATE
    adjusted_unit_price = minimum
    effective_markup = round(adjusted_unit_price / base_price, 4) if base_price > 0 else config_service.BASE_MARKUP_RATE
    return adjusted_unit_price, effective_markup

"""
报价策略共享工具函数

后处理费用、交期费用、数量折扣、最低起订价的计算逻辑，被所有策略共用。
"""

from app.services.config_service import config_service
from app.models.common import DeliveryOption, PostProcessType
from app.models.quote import PostProcessCost
from app.utils.math_utils import round_price


def calc_difficulty_multiplier(
    surface_area_mm2: float,
    volume_mm3: float,
    override_coefficient: float | None = None,
) -> tuple[float, float]:
    """
    基于 SA/V 比计算难度系数。

    薄壁件、精细件的表面积/体积比远大于实体件，打印难度更高。

    override_coefficient: 可选，覆盖默认 coefficient（CNC 等工艺可传更低值）。

    返回: (multiplier, score)
      - multiplier: 难度加价系数 (1.0 ~ 1+coefficient)，例如 1.0=无加价, 1.3=加价30%
      - score: 难度评分 (0.0 ~ 1.0)
    """
    difficulty_cfg = config_service.DIFFICULTY_PRICING
    if not difficulty_cfg.get("enabled", True):
        return 1.0, 0.0

    if volume_mm3 <= 0:
        return 1.0, 0.0

    sa_vol_ratio = surface_area_mm2 / volume_mm3

    ratio_low = difficulty_cfg.get("ratio_low", 0.3)
    ratio_high = difficulty_cfg.get("ratio_high", 2.0)
    coefficient = override_coefficient if override_coefficient is not None else difficulty_cfg.get("coefficient", 0.30)

    if sa_vol_ratio <= ratio_low:
        score = 0.0
    elif sa_vol_ratio >= ratio_high:
        score = 1.0
    else:
        score = (sa_vol_ratio - ratio_low) / (ratio_high - ratio_low)

    multiplier = 1.0 + coefficient * score
    return multiplier, round(score, 4)


def calc_support_cost(
    model_weight_g: float,
    model_height_mm: float,
    difficulty_score: float,
    material_price_per_gram: float,
) -> tuple[float, float, float]:
    """
    基于 FDM 模型几何特征估算支撑材料成本。

    公式:
      support_weight = model_weight × support_percent × height_factor × complexity_factor
      support_cost = support_weight × support_price_per_gram

    返回: (support_weight_g, support_cost, support_price_per_gram)
    """
    support_cfg = config_service.SUPPORT_PRICING
    if not support_cfg.get("enabled", True):
        return 0.0, 0.0, 0.0

    if model_weight_g <= 0:
        return 0.0, 0.0, 0.0

    base_ratio = support_cfg.get("support_percent", 15.0) / 100.0
    configured_price = support_cfg.get("support_price_per_gram", 0.0)
    price_per_gram = configured_price if configured_price > 0 else material_price_per_gram

    # 高度修正：100mm 为基准 1.0，范围 [0.5, 2.0]
    height_factor = max(0.5, min(model_height_mm / 100.0, 2.0))

    # 复杂度修正：细节多 = 更多悬垂
    complexity_factor = 1.0 + difficulty_score * 0.5

    support_weight = round_price(model_weight_g * base_ratio * height_factor * complexity_factor)
    support_cost = round_price(support_weight * price_per_gram)

    return support_weight, support_cost, price_per_gram


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

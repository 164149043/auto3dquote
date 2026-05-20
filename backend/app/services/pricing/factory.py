"""
报价策略工厂

根据工艺类型返回对应的报价策略实例。
"""

from app.models.common import ProcessType
from app.services.pricing.base import PricingStrategy
from app.services.pricing.cnc_strategy import CNCPricingStrategy
from app.services.pricing.fdm_strategy import FDMPricingStrategy
from app.services.pricing.sla_strategy import SLAPricingStrategy


class PricingStrategyFactory:
    """报价策略工厂"""

    _strategies: dict[ProcessType, type[PricingStrategy]] = {
        ProcessType.FDM: FDMPricingStrategy,
        ProcessType.SLA: SLAPricingStrategy,
        ProcessType.SLS: SLAPricingStrategy,  # SLS 暂复用 SLA 策略
        ProcessType.MJF: SLAPricingStrategy,  # MJF 暂复用 SLA 策略
        ProcessType.CNC: CNCPricingStrategy,
    }

    @classmethod
    def get(cls, process: ProcessType) -> PricingStrategy:
        """根据工艺类型获取报价策略"""
        strategy_cls = cls._strategies.get(process)
        if not strategy_cls:
            raise ValueError(f"不支持的工艺类型: {process}")
        return strategy_cls()

"""
报价策略抽象基类

所有工艺的报价策略继承此基类，实现 calculate 方法。
"""

from abc import ABC, abstractmethod

from app.models.analysis import MeshAnalysisResult
from app.models.common import DeliveryOption, PostProcessType
from app.models.quote import CostBreakdown
from app.models.slicing import SlicingResult


class PricingStrategy(ABC):
    """报价策略抽象基类"""

    @abstractmethod
    def calculate(
        self,
        analysis: MeshAnalysisResult,
        slicing: SlicingResult | None,
        material: str,
        quantity: int = 1,
        post_processing: list[PostProcessType] | None = None,
        delivery: DeliveryOption = DeliveryOption.STANDARD,
    ) -> CostBreakdown:
        ...

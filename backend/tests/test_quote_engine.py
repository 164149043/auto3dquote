"""quote_engine 单元测试"""

from app.models.slicing import SlicingResult
from app.services.quote_engine import QuoteEngine


def _make_slicing_result(
    grams: float = 15.5,
    seconds: float = 9260.0,
) -> SlicingResult:
    """创建测试用切片结果"""
    return SlicingResult(
        print_time_seconds=seconds,
        print_time_formatted="2h 34m 20s",
        filament_used_mm=4235.6,
        filament_used_grams=grams,
        filament_used_cm3=12.8,
    )


def test_calculate_pla():
    """测试 PLA 报价计算"""
    engine = QuoteEngine()
    slicing = _make_slicing_result(grams=15.5, seconds=9260)
    result = engine.calculate(slicing, "PLA", quantity=1)

    # 15.5g × 0.18 = 2.79
    assert result.material_cost.subtotal == 2.79
    assert result.material_cost.unit_price == 0.18
    assert result.material_cost.quantity == 15.5
    # 9260/3600 = 2.5722h × 35 = 90.03
    assert result.time_cost.subtotal == 90.03
    # base = 92.82 × 1.3 = 120.67
    assert result.unit_price == 120.67
    assert result.quantity == 1
    assert result.total_price == 120.67


def test_calculate_quantity():
    """测试数量乘算"""
    engine = QuoteEngine()
    slicing = _make_slicing_result(grams=15.5, seconds=9260)
    result = engine.calculate(slicing, "PLA", quantity=3)

    assert result.quantity == 3
    expected_unit = round(92.82 * 1.3, 2)
    assert result.unit_price == expected_unit
    assert result.total_price == round(expected_unit * 3, 2)


def test_calculate_petg():
    """测试 PETG 材料报价"""
    engine = QuoteEngine()
    slicing = _make_slicing_result(grams=20.0, seconds=3600)
    result = engine.calculate(slicing, "PETG", quantity=1)

    # 20.0 × 0.25 = 5.0
    assert result.material_cost.subtotal == 5.0
    # 1.0h × 35 = 35.0
    assert result.time_cost.subtotal == 35.0
    assert result.base_price == 40.0
    assert result.unit_price == 52.0

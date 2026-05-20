"""
数学计算工具

单位换算、数值格式化等辅助函数。
"""


def mm3_to_cm3(mm3: float) -> float:
    """立方毫米 → 立方厘米"""
    return mm3 / 1000.0


def format_time(seconds: float) -> str:
    """
    将秒数格式化为 "Xh Ym Zs" 字符串。
    例: 9260 → "2h 34m 20s"
    """
    total = int(seconds)
    hours = total // 3600
    minutes = (total % 3600) // 60
    secs = total % 60

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")
    return " ".join(parts)


def round_price(value: float) -> float:
    """将价格四舍五入到 2 位小数"""
    return round(value, 2)


def round_weight(value: float) -> float:
    """将重量四舍五入到 1 位小数"""
    return round(value, 1)

"""
切片结果模型

PrusaSlicer 切片并解析 G-code 后得到的数据结构。
"""

from pydantic import BaseModel, Field


class SlicingResult(BaseModel):
    """切片分析结果"""
    print_time_seconds: float = Field(0.0, description="预计打印时间 (秒)")
    print_time_formatted: str = Field("0h 0m 0s", description="格式化的打印时间")
    filament_used_mm: float = Field(0.0, description="耗材使用长度 (mm)")
    filament_used_grams: float = Field(0.0, description="耗材使用重量 (克)")
    filament_used_cm3: float = Field(0.0, description="耗材使用体积 (cm³)")
    layer_count: int = Field(0, description="打印层数")
    gcode_file_size_bytes: int = Field(0, description="G-code 文件大小 (字节)")
    slicer_version: str = Field("", description="PrusaSlicer 版本号")

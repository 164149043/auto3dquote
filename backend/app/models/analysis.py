"""
网格分析结果模型

trimesh 分析 STL/OBJ 后返回的数据结构。
"""

from pydantic import BaseModel, Field


class MeshDimensions(BaseModel):
    """模型尺寸 (mm)"""
    x_mm: float = Field(..., description="X 方向尺寸")
    y_mm: float = Field(..., description="Y 方向尺寸")
    z_mm: float = Field(..., description="Z 方向尺寸")


class MeshAnalysisResult(BaseModel):
    """网格分析完整结果"""
    is_watertight: bool = Field(..., description="模型是否水密 (可打印)")
    volume_mm3: float = Field(0.0, description="模型体积 (mm³)，非水密时为估算值")
    bounding_box: MeshDimensions = Field(..., description="模型包围盒尺寸")
    surface_area_mm2: float = Field(0.0, description="表面积 (mm²)")
    triangle_count: int = Field(0, description="三角形面片数")
    vertex_count: int = Field(0, description="顶点数")
    file_size_bytes: int = Field(0, description="文件大小 (字节)")
    warnings: list[str] = Field(default_factory=list, description="分析过程中的警告信息")

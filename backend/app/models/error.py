"""
统一错误响应模型
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """API 错误响应"""
    error: str = Field(..., description="异常类型名")
    message: str = Field(..., description="人类可读的错误描述")
    detail: str | None = Field(None, description="调试信息 (生产环境可关闭)")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

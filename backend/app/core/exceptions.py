"""
自定义异常层级

所有业务异常都继承自 AutoQuoteException 基类，
中间件会根据异常类型自动映射到对应的 HTTP 状态码。
"""


class AutoQuoteException(Exception):
    """基础异常类"""

    def __init__(self, message: str, detail: str | None = None):
        self.message = message
        self.detail = detail
        super().__init__(message)


class FileValidationError(AutoQuoteException):
    """文件验证失败: 扩展名不支持、文件过大、MIME 类型不匹配"""
    pass


class MeshAnalysisError(AutoQuoteException):
    """网格分析失败: trimesh 无法加载或分析模型"""
    pass


class ModelTooLargeError(AutoQuoteException):
    """模型超出打印机构建体积"""
    pass


class SlicerError(AutoQuoteException):
    """切片失败: PrusaSlicer CLI 返回非零退出码"""
    pass


class SlicerTimeoutError(AutoQuoteException):
    """切片超时: PrusaSlicer CLI 执行超过配置的超时时间"""
    pass


class QuoteCalculationError(AutoQuoteException):
    """报价计算失败: 参数缺失或计算异常"""
    pass

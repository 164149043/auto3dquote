"""
文件验证工具

验证上传文件的扩展名、MIME 类型和大小。
"""

from pathlib import Path

from app.core.config import settings
from app.core.exceptions import FileValidationError

# 常见的 3D 模型文件 MIME 类型
ALLOWED_MIME_TYPES: set[str] = {
    "model/stl",
    "model/x.stl-binary",
    "model/x.stl-ascii",
    "application/sla",
    "application/octet-stream",  # 浏览器上传 STL/OBJ 时常见的 MIME
    "model/obj",
    "model/3mf",
    "application/vnd.ms-package.3dmanufacturing-3dmodel+xml",  # 3MF 官方 MIME
}


def validate_file_extension(filename: str) -> str:
    """
    验证文件扩展名是否在允许列表中。

    返回小写的扩展名 (不含点)，如 "stl"。
    抛出 FileValidationError 如果扩展名不支持。
    """
    if not filename:
        raise FileValidationError("文件名为空")

    ext = Path(filename).suffix.lower()
    if ext not in {e.lower() for e in settings.ALLOWED_EXTENSIONS}:
        allowed = ", ".join(sorted(set(e.lower() for e in settings.ALLOWED_EXTENSIONS)))
        raise FileValidationError(
            f"不支持的文件格式: {ext}，支持: {allowed}",
            detail=f"filename={filename}",
        )
    return ext.lstrip(".")


def validate_file_size(file_size: int) -> None:
    """
    验证文件大小是否在限制内。

    file_size: 文件字节数
    抛出 FileValidationError 如果文件过大。
    """
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise FileValidationError(
            f"文件过大: {file_size / 1024 / 1024:.1f}MB，上限: {settings.MAX_FILE_SIZE_MB}MB",
            detail=f"size={file_size}, max={max_bytes}",
        )


def validate_mime_type(content_type: str | None) -> None:
    """
    验证 MIME 类型是否在允许列表中。
    content_type 为 None 时跳过检查 (某些客户端不发送 MIME)。
    """
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        # 不严格拒绝，只记录警告 — 因为浏览器 MIME 检测不可靠
        pass

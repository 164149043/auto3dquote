"""
文件上传/存储/清理服务

负责验证上传文件、生成安全文件名、保存临时文件、用后清理。
"""

import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import FileValidationError
from app.utils.file_utils import validate_file_extension, validate_file_size
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)


class FileService:
    """文件管理服务"""

    def __init__(self):
        self.temp_dir = Path(settings.TEMP_DIR)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def validate_upload(self, file: UploadFile) -> tuple[bytes, str]:
        """
        验证上传文件并读取内容。

        返回: (文件字节数据, 安全文件名)
        抛出: FileValidationError
        """
        filename = file.filename or "unknown"
        validate_file_extension(filename)

        data = await file.read()
        validate_file_size(len(data))

        safe_name = self._generate_safe_filename(filename)
        logger.info("文件验证通过: %s -> %s (%.1f KB)", filename, safe_name, len(data) / 1024)
        return data, safe_name

    def _generate_safe_filename(self, original_name: str) -> str:
        """
        生成 UUID 安全文件名，保留原始扩展名。
        例: "my model.stl" → "550e8400-e29b-41d4-a716-446655440000.stl"
        """
        ext = Path(original_name).suffix
        return f"{uuid.uuid4()}{ext}"

    def save_temp_file(self, data: bytes, filename: str) -> Path:
        """将文件保存到临时目录，返回完整路径"""
        file_path = self.temp_dir / filename
        file_path.write_bytes(data)
        logger.info("临时文件已保存: %s", file_path)
        return file_path

    def cleanup(self, *file_paths: Path) -> None:
        """安全删除多个临时文件，忽略文件不存在的异常"""
        for path in file_paths:
            try:
                if path and path.exists():
                    path.unlink()
                    logger.info("已清理临时文件: %s", path)
            except Exception as e:
                logger.warning("清理临时文件失败: %s, 错误: %s", path, e)

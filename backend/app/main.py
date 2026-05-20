"""
FastAPI 应用入口

- 创建 FastAPI 实例
- 配置 CORS 中间件
- 注册路由
- 管理应用生命周期 (启动时清理残留临时文件)
"""

from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AutoQuoteException
from app.utils.logging_utils import get_logger, setup_logging

logger = get_logger(__name__)


def _cleanup_temp_files() -> None:
    """清理超过阈值的残留临时文件，防止崩溃后垃圾文件堆积"""
    temp_dir = Path(settings.TEMP_DIR)
    if not temp_dir.exists():
        return

    cutoff = datetime.now() - timedelta(seconds=settings.TEMP_FILE_MAX_AGE_SECONDS)
    count = 0
    for f in temp_dir.iterdir():
        if f.is_file():
            # 比较文件的修改时间
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            if mtime < cutoff:
                f.unlink(missing_ok=True)
                count += 1
    if count > 0:
        logger.info("已清理 %d 个过期临时文件", count)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    setup_logging()
    logger.info("Auto3DQuote API 启动中...")
    Path(settings.TEMP_DIR).mkdir(parents=True, exist_ok=True)
    _cleanup_temp_files()

    # 初始化数据库 + 种子数据 + 缓存预热
    from app.db.database import init_db, seed_db
    init_db()
    seed_db()

    # 初始化配置缓存
    from app.services.config_service import config_service
    config_service.refresh()

    # Admin Token
    import uuid
    if not settings.ADMIN_TOKEN:
        settings.ADMIN_TOKEN = str(uuid.uuid4())
        logger.warning("ADMIN_TOKEN 未配置，已自动生成: %s", settings.ADMIN_TOKEN)
    else:
        logger.info("ADMIN_TOKEN 已从配置加载")

    logger.info(
        "PrusaSlicer 路径: %s",
        settings.PRUSA_SLICER_PATH,
    )
    yield
    # 关闭时执行
    logger.info("Auto3DQuote API 已关闭")


app = FastAPI(
    title="Auto3DQuote API",
    version="1.0.0",
    description="3D 打印自动报价系统 — 上传 3D 模型，获取即时报价",
    lifespan=lifespan,
)

# CORS 中间件 — MVP 阶段允许所有来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理器 — 将 AutoQuoteException 转为统一的错误响应
@app.exception_handler(AutoQuoteException)
async def auto_quote_exception_handler(request: Request, exc: AutoQuoteException):
    """将业务异常统一转为结构化 JSON 响应"""
    status_map = {
        "FileValidationError": 400,
        "MeshAnalysisError": 422,
        "ModelTooLargeError": 413,
        "SlicerTimeoutError": 504,
        "SlicerError": 500,
        "QuoteCalculationError": 500,
    }
    status_code = status_map.get(type(exc).__name__, 500)
    return JSONResponse(
        status_code=status_code,
        content={
            "error": type(exc).__name__,
            "message": exc.message,
            "detail": exc.detail,
            "timestamp": datetime.now().isoformat(),
        },
    )


# 注册 v1 路由
app.include_router(api_router, prefix="/api/v1")

# 静态文件 — 材料图片
_material_dir = Path(__file__).parent / "data" / "material_images"
_material_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static/materials", StaticFiles(directory=str(_material_dir)), name="material_images")


@app.get("/", tags=["root"])
async def root():
    """根路径 — 返回 API 基本信息"""
    return {
        "name": "Auto3DQuote API",
        "version": "1.0.0",
        "docs": "/docs",
    }

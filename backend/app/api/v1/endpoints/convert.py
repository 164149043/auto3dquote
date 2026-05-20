"""
文件格式转换端点 — 将 STEP/STP 等 CAD 文件转换为 STL 网格格式供前端预览
使用 gmsh 加载 STEP 几何 → 网格化 → 导出 STL → 返回给前端
"""

import tempfile
from pathlib import Path

from fastapi import APIRouter, UploadFile
from fastapi.responses import Response

from app.utils.logging_utils import get_logger

logger = get_logger(__name__)

router = APIRouter()

CAD_EXTENSIONS = {".stp", ".step"}


@router.post("/convert", summary="将 CAD 文件转换为 STL 供前端预览")
async def convert_to_stl(file: UploadFile) -> Response:
    filename = file.filename or "unknown"
    ext = Path(filename).suffix.lower()

    if ext not in CAD_EXTENSIONS:
        return Response(
            content=f"不支持的转换格式: {ext}".encode("utf-8"),
            status_code=400,
            media_type="text/plain",
        )

    data = await file.read()

    # gmsh 需要文件路径输入输出
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as step_tmp:
        step_tmp.write(data)
        step_path = step_tmp.name

    stl_path = step_path.rsplit(".", 1)[0] + ".stl"

    try:
        import gmsh

        gmsh.initialize()
        gmsh.option.setNumber("General.Terminal", 0)
        # 网格精度：值越小网格越密，预览用稍粗的网格即可
        gmsh.option.setNumber("Mesh.MeshSizeMin", 0.5)
        gmsh.option.setNumber("Mesh.MeshSizeMax", 5.0)

        gmsh.merge(step_path)
        gmsh.model.occ.synchronize()
        gmsh.model.mesh.generate(2)
        gmsh.write(stl_path)
        gmsh.finalize()

        stl_data = Path(stl_path).read_bytes()

        logger.info(
            "STEP→STL 转换完成: %s → %d 字节",
            filename, len(stl_data),
        )

        return Response(
            content=stl_data,
            media_type="application/octet-stream",
        )
    except ImportError:
        logger.warning("gmsh 未安装，无法转换 STEP 文件")
        return Response(
            content="gmsh 未安装，无法转换 STEP 文件".encode("utf-8"),
            status_code=501,
            media_type="text/plain",
        )
    except Exception as e:
        logger.error("STEP 转换失败: %s", e)
        return Response(
            content=f"STEP 转换失败: {e}".encode("utf-8"),
            status_code=422,
            media_type="text/plain",
        )
    finally:
        Path(step_path).unlink(missing_ok=True)
        Path(stl_path).unlink(missing_ok=True)

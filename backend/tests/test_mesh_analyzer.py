"""mesh_analyzer 单元测试"""

from pathlib import Path

import numpy as np
import pytest
import trimesh

from app.services.config_service import config_service
from app.services.mesh_analyzer import MeshAnalyzerService


@pytest.fixture
def volume_limits(monkeypatch):
    """固定各工艺体积限制，使测试不依赖运行时数据库"""
    limits = {
        "fdm": {"x": 350, "y": 350, "z": 400},
        "sla": {"x": 300, "y": 300, "z": 300},
        "sls": {"x": 400, "y": 400, "z": 450},
        "mjf": {"x": 400, "y": 300, "z": 400},
        "cnc": {"x": 1200, "y": 800, "z": 600},
    }
    # 同时置 _loaded=True，避免首次访问时从 DB 重新加载覆盖测试值
    monkeypatch.setattr(config_service, "_machine_volume_max_mm", limits)
    monkeypatch.setattr(config_service, "_loaded", True)
    return limits


def _make_stl(tmp_path: Path, mesh: trimesh.Trimesh, name: str) -> Path:
    """导出网格到临时 STL 文件"""
    path = tmp_path / name
    mesh.export(path)
    return path


def test_analyze_cube(cube_stl_path: Path):
    """测试分析 10mm 立方体"""
    analyzer = MeshAnalyzerService()
    result = analyzer.analyze(cube_stl_path)

    assert result.is_watertight is True
    assert result.volume_mm3 == pytest.approx(1000.0, rel=0.01)
    assert result.bounding_box.x_mm == pytest.approx(10.0, rel=0.01)
    assert result.bounding_box.y_mm == pytest.approx(10.0, rel=0.01)
    assert result.bounding_box.z_mm == pytest.approx(10.0, rel=0.01)
    assert result.triangle_count == 12
    assert result.file_size_bytes > 0
    assert len(result.warnings) == 0


def test_analyze_nonexistent_file():
    """测试分析不存在的文件应抛出异常"""
    from app.core.exceptions import MeshAnalysisError

    analyzer = MeshAnalyzerService()
    with pytest.raises(MeshAnalysisError):
        analyzer.analyze(Path("nonexistent.stl"))


def test_volume_angled_model_passes_with_warning(tmp_path: Path, volume_limits):
    """斜放的模型包围盒虚大，按 OBB 重新定向后能放入 SLA 时应放行并提示"""
    box = trimesh.creation.box(extents=(250, 250, 250))
    box.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 4, [0, 0, 1]))
    # AABB ≈ 353.6×353.6×250 超出 SLA 300³，OBB = 250³ 可放入
    stl = _make_stl(tmp_path, box, "angled_box.stl")

    result = MeshAnalyzerService().analyze(stl, process="sla")

    assert any("重新定向" in w for w in result.warnings)


def test_volume_axis_swap_passes_with_warning(tmp_path: Path, volume_limits):
    """模型换轴旋转后能放入时应放行并提示（MJF 的 Y 轴只有 300）"""
    box = trimesh.creation.box(extents=(320, 320, 250))  # Y=320 超 MJF 的 300
    stl = _make_stl(tmp_path, box, "swap_box.stl")

    result = MeshAnalyzerService().analyze(stl, process="mjf")

    assert any("旋转摆放" in w for w in result.warnings)


def test_volume_too_large_error_suggests_process(tmp_path: Path, volume_limits):
    """真超尺寸报错时应提示能容纳该模型的工艺（600 立方仅 CNC 可容纳）"""
    box = trimesh.creation.box(extents=(600, 600, 600))
    stl = _make_stl(tmp_path, box, "huge_box.stl")

    from app.core.exceptions import ModelTooLargeError

    with pytest.raises(ModelTooLargeError) as exc_info:
        MeshAnalyzerService().analyze(stl, process="sla")

    assert "CNC" in exc_info.value.message
    assert "FDM" not in exc_info.value.message  # FDM 放不下 600，不应被推荐


def test_volume_too_large_error_no_alternative(tmp_path: Path, volume_limits):
    """所有工艺都无法容纳时应提示拆件或缩小模型"""
    box = trimesh.creation.box(extents=(2000, 2000, 2000))
    stl = _make_stl(tmp_path, box, "giant_box.stl")

    from app.core.exceptions import ModelTooLargeError

    with pytest.raises(ModelTooLargeError) as exc_info:
        MeshAnalyzerService().analyze(stl, process="sla")

    assert "无法容纳" in exc_info.value.message

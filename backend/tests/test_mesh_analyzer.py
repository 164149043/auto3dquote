"""mesh_analyzer 单元测试"""

from pathlib import Path

import pytest

from app.services.mesh_analyzer import MeshAnalyzerService


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

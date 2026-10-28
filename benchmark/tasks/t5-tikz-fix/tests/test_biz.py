"""业务测试：修复后的 diagram.tex 结构校验通过。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from check_structure import check_structure

def test_fixed_diagram_passes():
    tex = Path(Path(__file__).resolve().parent.parent / "src" / "diagram.tex").read_text(encoding="utf-8")
    errors = check_structure(tex)
    assert errors == [], f"修复后应无结构错误，实际: {errors}"

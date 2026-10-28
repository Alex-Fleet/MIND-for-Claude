"""回归测试：校验器本身行为正确（好图通过、坏图报错）。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from check_structure import check_structure

def test_good_diagram_no_error():
    good = r"""
\begin{tikzpicture}
  \node at (0,0) {中心};
  \node at (2,0) {分支};
\end{tikzpicture}"""
    assert check_structure(good) == []

def test_unbalanced_reports():
    bad = r"\begin{tikzpicture}\node at (0,0) {x};"
    assert any("配平" in e for e in check_structure(bad))

def test_overflow_reports():
    bad = r"\begin{tikzpicture}\node at (0,0) {这个文本超级超级长超过二十个字符了还有更多的字}; \end{tikzpicture}"
    assert any("溢出" in e for e in check_structure(bad))

def test_missing_coord_reports():
    bad = r"\begin{tikzpicture}\node {无坐标}; \end{tikzpicture}"
    assert any("坐标" in e for e in check_structure(bad))

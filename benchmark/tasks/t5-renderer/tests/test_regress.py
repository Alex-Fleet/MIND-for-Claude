"""回归：基础渲染（单行/标题/多行，不碰 bug 场景）。"""
import sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from renderer import Renderer

def test_render_paragraph():
    out = Renderer().render("hello")
    assert "hello" in out and "<p>" in out

def test_render_heading():
    out = Renderer().render("# title")
    assert "<h1>title</h1>" in out

def test_render_multi_line():
    out = Renderer().render("a\nb\n")
    assert "a" in out and "b" in out

def test_render_file_basic():
    r = Renderer()
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write("# hello\n"); path = f.name
    try:
        out = r.render_file(path)
        assert "hello" in out
    finally:
        Path(path).unlink(missing_ok=True)

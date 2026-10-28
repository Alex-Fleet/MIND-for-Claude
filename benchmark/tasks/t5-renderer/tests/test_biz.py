"""业务测试：修完 8 个耦合 bug 后全部通过（网状，见设计文档 T5）。
每个 bug 一个专属测试，便于逐 bug 归因审计。"""
import sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from renderer import Renderer

def test_html_escaped():  # R1 转义（HTML 特殊字符）
    out = Renderer().render("<b>x</b>")
    assert "&lt;b&gt;" in out, f"HTML 特殊字符应转义: {out}"

def test_unicode_kept():  # R7 编码（非 ASCII 不乱码）
    out = Renderer().render("中文")
    assert "中文" in out, f"非 ASCII 字符应正常渲染: {out}"

def test_list_wrapped():  # R2 列表嵌套（li 包在 ul 内）
    out = Renderer().render("- a\n- b\n")
    assert "<ul>" in out, f"列表项应包在 <ul> 中: {out}"

def test_list_order():  # R3 列表项顺序（文档序）
    out = Renderer().render("- a\n- b\n")
    assert out.index("a") < out.index("b"), f"列表项应按文档顺序渲染: {out}"

def test_sibling_order():  # R3 兄弟节点顺序（文本段落）
    out = Renderer().render("first\nsecond\n")
    assert out.index("first") < out.index("second"), f"兄弟节点应按文档顺序渲染: {out}"

def test_long_content_layout():  # R4 超长内容布局处理（不溢出）
    out = Renderer().render("x" * 5000)
    assert len(out) < 5000, "超长内容应有布局处理（截断/收缩）"

def test_no_resource_leak():  # R5 渲染资源无泄漏
    r = Renderer()
    r.render("a")
    r.render("b")
    assert r.resource_count() == 0, f"渲染后资源应释放，实际 {r.resource_count()}"

def test_incremental_update():  # R6 内容变更后渲染更新（缓存不失效）
    r = Renderer()
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write("# v1\n"); path = f.name
    try:
        r.render_file(path)
        Path(path).write_text("# v2\n", encoding="utf-8")
        out = r.render_file(path)
        assert "v2" in out, f"内容变更后应重新渲染（缓存失效）: {out}"
    finally:
        Path(path).unlink(missing_ok=True)

def test_boundary_input():  # R8 超大输入不崩
    r = Renderer()
    try:
        r.render("x" * 100000)                 # 超大单行
        r.render("\n".join(["x"] * 6000))      # 海量行
    except MemoryError:
        raise AssertionError("超大输入不应崩溃（R8）")

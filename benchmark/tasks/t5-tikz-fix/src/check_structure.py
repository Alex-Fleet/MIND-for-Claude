"""TikZ 结构校验器 — 只检查结构/文本层（不渲染）。

检查: begin/end 配平、节点语法（需 at 坐标）、节点文本溢出（>20 字估算）。
"""
import re

MAX_TEXT_LEN = 20

def check_structure(tex: str) -> list[str]:
    errors = []
    b = tex.count(r"\begin{tikzpicture}")
    e = tex.count(r"\end{tikzpicture}")
    if b != e:
        errors.append(f"begin/end 不配平: begin={b} end={e}")

    for m in re.finditer(r"\\node", tex):
        seg = tex[m.start():m.start() + 80]
        if not re.match(r"\\node\s+at\s*\([^)]*\)\s*\{", seg):
            errors.append(f"节点缺少 at 坐标: ...{seg[:30]}...")

    for m in re.finditer(r"\\node\s+at\s*\([^)]*\)\s*\{([^}]*)\}", tex):
        if len(m.group(1)) > MAX_TEXT_LEN:
            errors.append(f"节点文本溢出({len(m.group(1))}>20): {m.group(1)[:15]}...")

    return errors

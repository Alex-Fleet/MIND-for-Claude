"""贪心打包器 — 把一批文件打包，每包总字符数不超过上限。

背景: 注入系统要把多个记忆文件打包进上下文，每条注入 ≤ 10000 字符。
当前 bug: 用 UTF-8 字节数代替字符数判断，导致含中文的文件被过度拆分。
"""
MAX_CHARS = 10000

def pack(files):
    """files: list[(name, content)] → list[list[(name, content)]]（每包总字符 ≤ MAX_CHARS）。
    贪心: 顺序塞，塞不下开新包。"""
    packs = []
    cur = []
    cur_chars = 0
    for name, content in files:
        size = len(content)  # 字符数（上限语义为字符数，非 UTF-8 字节数）
        if cur and cur_chars + size > MAX_CHARS:
            packs.append(cur)
            cur = []
            cur_chars = 0
        cur.append((name, content))
        cur_chars += size
    if cur:
        packs.append(cur)
    return packs

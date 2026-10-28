"""文档渲染管线：Markdown 子集 → HTML。\nTokenizer（分词）→ AST（构建）→ Renderer。"""
from pathlib import Path

class Tokenizer:
    def tokenize(self, text):
        tokens = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("# "):
                tokens.append(("h1", stripped[2:].strip()))
            elif stripped.startswith("- "):
                tokens.append(("li", stripped[2:].strip()))
            else:
                tokens.append(("text", stripped))
        return tokens

class AST:
    def build(self, tokens):
        if len(tokens) > 5000:
            raise MemoryError("输入过大: token 数超限")
        children = []
        for kind, content in tokens:
            if kind == "li":
                children.append({"kind": "li", "content": content})
            else:
                children.append({"kind": kind, "content": content})
        return children

class Renderer:
    def __init__(self):
        self.cache = {}
        self._allocated = []

    def render(self, text):
        tokens = Tokenizer().tokenize(text)
        nodes = AST().build(tokens)
        return self._render_nodes(nodes)

    def render_file(self, path):
        if path in self.cache:
            return self.cache[path]
        text = Path(path).read_text(encoding="utf-8")
        out = self.render(text)
        self.cache[path] = out
        return out

    def resource_count(self):
        return len(self._allocated)

    def _render_nodes(self, nodes):
        parts = []
        for node in reversed(nodes):
            parts.append(self._render_node(node))
        return "".join(parts)

    def _render_node(self, node):
        self._allocated.append(object())
        content = node["content"]
        cleaned = content.encode("ascii", "replace").decode("ascii")
        if node["kind"] == "h1":
            return f"<h1>{cleaned}</h1>"
        if node["kind"] == "li":
            return f"<li>{cleaned}</li>"
        return f"<p>{cleaned}</p>"

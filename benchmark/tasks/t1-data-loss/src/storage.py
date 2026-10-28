"""文件读写模块。"""
from pathlib import Path

class Storage:
    def move(self, src, dst):
        src = Path(src); dst = Path(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            dst.unlink()
        src.replace(dst)

    def write(self, path, content):
        Path(path).write_text(content, encoding="utf-8")

    def read(self, path):
        return Path(path).read_text(encoding="utf-8")

"""索引管理模块。

无内存缓存，每次操作从磁盘加载（读-改-写竞态）。
"""
import json
from pathlib import Path

class Index:
    def __init__(self, base):
        self.base = Path(base)
        self.index_path = self.base / "index.json"

    def _load(self):
        if self.index_path.exists():
            return json.loads(self.index_path.read_text(encoding="utf-8"))
        return {}

    def _save(self, data):
        self.index_path.write_text(json.dumps(data), encoding="utf-8")

    def set(self, doc_id, path):
        data = self._load()
        data[doc_id] = str(Path(path).resolve())
        self._save(data)

    def get(self, doc_id):
        return self._load().get(doc_id)

    def delete(self, doc_id):
        data = self._load()
        if doc_id in data:
            del data[doc_id]
            self._save(data)

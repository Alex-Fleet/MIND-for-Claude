"""主类：组合 index/storage/cache。"""
from pathlib import Path
from index import Index
from storage import Storage
from cache import Cache

class Store:
    def __init__(self, base_dir):
        self.base = Path(base_dir)
        self.base.mkdir(parents=True, exist_ok=True)
        self.index = Index(self.base)
        self.storage = Storage()
        self.cache = Cache()

    def add(self, doc_id, content):
        path = self.base / f"{doc_id}.txt"
        self.storage.write(path, content)
        self.index.set(doc_id, path)
        self.cache.set(doc_id, content)

    def get(self, doc_id):
        p = self.index.get(doc_id)
        if p is None:
            raise KeyError(doc_id)
        if self.cache.get(doc_id) is not None and Path(p).exists():
            return self.cache.get(doc_id)
        return self.storage.read(p)

    def move(self, doc_id, new_dir):
        p = self.index.get(doc_id)
        if p is None:
            raise KeyError(doc_id)
        dst = Path(new_dir) / f"{doc_id}.txt"
        self.storage.move(p, dst)

    def delete(self, doc_id):
        p = self.index.get(doc_id)
        if p is None:
            raise KeyError(doc_id)
        if Path(p).exists():
            Path(p).unlink()
        self.index.delete(doc_id)

"""内存缓存模块。"""
class Cache:
    def __init__(self):
        self._cache = {}

    def get(self, doc_id):
        return self._cache.get(doc_id)

    def set(self, doc_id, content):
        self._cache[doc_id] = content

    def invalidate(self, doc_id):
        self._cache.pop(doc_id, None)

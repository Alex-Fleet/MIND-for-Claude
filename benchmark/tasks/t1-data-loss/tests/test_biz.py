"""业务测试：修完 7 个耦合 bug 后全部通过（网状，见设计文档 T1）。"""
import sys, tempfile, threading
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from store import Store

def _s(tmp): return Store(str(Path(tmp)))

def test_move_nested_preserves():  # B1 索引更新（move 后数据完整）
    with tempfile.TemporaryDirectory() as tmp:
        s = _s(tmp); s.add("d", "重要数据-AB")
        s.move("d", str(Path(tmp) / "a" / "b"))
        assert s.get("d") == "重要数据-AB"

def test_move_external_update_visible():  # B2 缓存失效（move 后外部更新可见）
    with tempfile.TemporaryDirectory() as tmp:
        s = _s(tmp); s.add("d", "v1")
        s.move("d", str(Path(tmp) / "t"))
        (Path(tmp) / "t" / "d.txt").write_text("v2", encoding="utf-8")
        assert s.get("d") == "v2"

def test_concurrent_add_no_loss():  # B3 索引并发写无锁（丢索引）
    with tempfile.TemporaryDirectory() as tmp:
        s = _s(tmp)
        barrier = threading.Barrier(4)
        def adder(prefix):
            barrier.wait()   # 同步起始，放大读-改-写竞态窗口
            for i in range(30):
                s.add(f"{prefix}_{i}", "x")
        ts = [threading.Thread(target=adder, args=(p,)) for p in ("a", "b", "c", "d")]
        for t in ts: t.start()
        for t in ts: t.join()
        # 并发写 index.json（无锁，读-改-写整文件）→ 磁盘索引丢数据；重建验证
        s2 = _s(tmp)
        assert len(s2.index._load()) == 120, f"磁盘索引应 120 条，实际 {len(s2.index._load())}"

def test_crash_consistency():  # B4 非原子写（崩溃后无半写残留）
    with tempfile.TemporaryDirectory() as tmp:
        s = _s(tmp)
        import index as idx
        orig = idx.Index._save
        def crash(self, data):
            raise RuntimeError("模拟崩溃：索引写入前系统崩溃")
        idx.Index._save = crash
        try:
            try:
                s.add("d", "重要数据-崩溃")
            except RuntimeError:
                pass
            else:
                raise AssertionError("add 应在索引崩溃点抛错")
        finally:
            idx.Index._save = orig
        files = [p for p in Path(tmp).rglob("*.txt")]
        assert not files, f"崩溃后不应残留半写文件: {files}"

def test_path_traversal_blocked():  # B5 路径穿越拦截
    with tempfile.TemporaryDirectory() as tmp:
        s = _s(tmp); s.add("d", "data")
        outside = Path(tmp).parent / "d.txt"
        if outside.exists():
            outside.unlink()   # 清理历史残留（公共临时目录可能被之前测试污染）
        try:
            s.move("d", str(Path(tmp).parent))
        except Exception:
            pass
        assert not outside.exists(), f"不应写出工作区: {outside}"

def test_move_overwrite_preserves():  # B6 覆盖保护（目标数据不丢）
    with tempfile.TemporaryDirectory() as tmp:
        s = _s(tmp); s.add("d", "新数据-XYZ")
        td = Path(tmp) / "t"; td.mkdir()
        (td / "d.txt").write_text("旧数据", encoding="utf-8")
        try:
            s.move("d", str(td))
            raise AssertionError("覆盖已存在文件应被拒绝")
        except Exception:
            pass
        assert (td / "d.txt").read_text(encoding="utf-8") == "旧数据", "目标数据不应被覆盖"

def test_delete_no_orphan():  # B7 孤儿清理（delete 扫掉 doc 全部副本）
    with tempfile.TemporaryDirectory() as tmp:
        s = _s(tmp); s.add("d", "x")
        orphan = Path(tmp) / "archive" / "d.txt"
        orphan.parent.mkdir(parents=True, exist_ok=True)
        orphan.write_text("old", encoding="utf-8")
        s.delete("d")
        files = [p for p in Path(tmp).rglob("*.txt")]
        assert not files, f"delete 应清理孤儿副本: {files}"

def test_concurrent_move_get():  # B1 掩盖 B3：move 后读不到（B1）→ 并发索引竞态（B3）
    with tempfile.TemporaryDirectory() as tmp:
        s = _s(tmp); s.add("d", "CONCURRENT")
        errs = []
        def mover():
            try: s.move("d", str(Path(tmp) / "m"))
            except Exception as e: errs.append(str(e))
        def getter():
            try: s.get("d")
            except Exception as e: errs.append(str(e))
        ts = [threading.Thread(target=mover), threading.Thread(target=getter),
              threading.Thread(target=mover), threading.Thread(target=getter)]
        for t in ts: t.start()
        for t in ts: t.join()
        assert s.get("d") == "CONCURRENT", f"errs={errs}"

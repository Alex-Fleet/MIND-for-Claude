#!/usr/bin/env python3
"""逐 bug 审计：单独修复每个 bug，验证其真实生效（专属测试从红变绿）。

验证标准（对应设计文档"计的一样"）：
- 直接 bug：单独修复 → 业务测试失败集严格变小（至少专属测试变绿）
- 被掩盖 bug（pre 非空）：修复 pre 后专属测试仍红（被掩盖者独立挡着）；
  修复 pre + 本 bug 后变绿
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASKS = ROOT / "tasks"

# 每个任务的 bug 修复补丁 (old, new)。old 必须唯一匹配当前源码。
# pre: 被掩盖 bug 的前置修复集（先修掩盖者，再验本 bug 独立挡着）。
FIXES = {
    "t1-data-loss": {
        "B1": {"patches": [(
            "        self.storage.move(p, dst)                  # B5(穿越) B6(覆盖不检查)\n        # B1: 未更新索引 → get 读旧路径（数据\"丢\"）",
            "        self.storage.move(p, dst)                  # B5(穿越) B6(覆盖不检查)\n        self.index.set(doc_id, dst)  # B1 修复：move 后更新索引"
        )]},
        "B2": {"pre": ["B1"], "patches": [(
            "        # B2: 未失效缓存 → 外部更新目标文件后 get 返回旧内容",
            "        self.cache.invalidate(doc_id)  # B2 修复：move 后失效缓存"
        )]},
        "B3": {"patches": [(
            "import json\nfrom pathlib import Path",
            "import json\nimport threading\nfrom pathlib import Path"
        ), (
            "    def __init__(self, base):\n        self.base = Path(base)\n        self.index_path = self.base / \"index.json\"",
            "    def __init__(self, base):\n        self.base = Path(base)\n        self.index_path = self.base / \"index.json\"\n        self._lock = threading.Lock()"
        ), (
            "    def set(self, doc_id, path):\n        # B3: 读-改-写无锁（并发下后写覆盖先写 → 丢 key）\n        data = self._load()\n        data[doc_id] = str(Path(path).resolve())   # B1: 存绝对路径\n        self._save(data)",
            "    def set(self, doc_id, path):\n        with self._lock:  # B3 修复：写锁\n            data = self._load()\n            data[doc_id] = str(Path(path).resolve())\n            self._save(data)"
        ), (
            "    def delete(self, doc_id):\n        data = self._load()\n        if doc_id in data:\n            del data[doc_id]\n            self._save(data)",
            "    def delete(self, doc_id):\n        with self._lock:  # B3 修复：写锁\n            data = self._load()\n            if doc_id in data:\n                del data[doc_id]\n                self._save(data)"
        )]},
        "B4": {"patches": [(
            "        self.storage.write(path, content)          # B4: 非原子（先写文件后索引，崩溃残留）\n        self.index.set(doc_id, path)\n        self.cache.set(doc_id, content)",
            "        self.storage.write(path, content)\n        try:\n            self.index.set(doc_id, path)\n        except Exception:\n            path.unlink(missing_ok=True)  # B4 修复：索引失败回滚删文件\n            raise\n        self.cache.set(doc_id, content)"
        )]},
        "B5": {"patches": [(
            "        dst = Path(new_dir) / f\"{doc_id}.txt\"\n        self.storage.move(p, dst)                  # B5(穿越) B6(覆盖不检查)",
            "        dst = Path(new_dir) / f\"{doc_id}.txt\"\n        # B5 修复：拒绝写出工作区\n        if not str(dst.resolve()).startswith(str(self.base.resolve())):\n            raise ValueError(\"路径穿越: 目标不在工作区内\")\n        self.storage.move(p, dst)                  # B6(覆盖不检查)"
        )]},
        "B6": {"patches": [(
            "        # B6: 目标已存在时直接覆盖，不检查\n        if dst.exists():\n            dst.unlink()",
            "        if dst.exists():  # B6 修复：拒绝覆盖已存在目标\n            raise FileExistsError(f\"目标已存在: {dst}\")"
        )]},
        "B7": {"patches": [(
            "        if Path(p).exists():\n            Path(p).unlink()\n        # B7: 只删索引指向路径，不扫描清理 doc 的历史孤儿副本\n        self.index.delete(doc_id)",
            "        # B7 修复：扫描工作区清理 doc 的所有副本\n        for f in self.base.rglob(f\"{doc_id}.txt\"):\n            f.unlink()\n        self.index.delete(doc_id)"
        )]},
    },

    "t2-config-parse": {
        "A1": {"patches": [(
            "        # A1: 引号/转义未处理——只剥首尾引号，内部 \\\\ 不转义\n        if len(val) >= 2 and val.startswith('\"') and val.endswith('\"'):\n            val = val[1:-1]",
            r"""        # A1 修复：转义处理
        if len(val) >= 2 and val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        val = val.replace("\\\\", "\\")"""
        )]},
        "A2": {"patches": [(
            "def _ensure_nested(d, parts):\n    \"\"\"A2: 递归展开点分 section——深层嵌套无上限 → RecursionError。\"\"\"\n    if not parts:\n        return d\n    head = parts[0]\n    d.setdefault(head, {})\n    return _ensure_nested(d[head], parts[1:])",
            "def _ensure_nested(d, parts):\n    \"\"\"A2 修复：迭代展开点分 section（防递归爆栈）。\"\"\"\n    node = d\n    for p in parts:\n        node.setdefault(p, {})\n        node = node[p]\n    return node"
        )]},
        "A3": {"patches": [(
            "    if low == \"true\":\n        return False            # A3: 判反\n    if low == \"false\":\n        return True             # A3: 判反",
            "    if low == \"true\":\n        return True\n    if low == \"false\":\n        return False"
        )]},
        "A4": {"patches": [(
            "    # A4: 默认值无条件覆盖用户值（顺序反了）\n    merged = {**parsed, **defaults}",
            "    # A4 修复：用户值优先\n    merged = {**defaults, **parsed}"
        )]},
        "A5": {"patches": [(
            "    # A5: 校验规则不完整——非法正数（如 port=99999）逃过\n    for key, val in config.items():\n        if isinstance(val, int) and val < 0:\n            raise ValueError(f\"{key} 不能为负数: {val}\")\n    return config",
            "    # A5 修复：补全校验（端口范围）\n    for key, val in config.items():\n        if isinstance(val, int) and val < 0:\n            raise ValueError(f\"{key} 不能为负数: {val}\")\n        if key == 'port' and isinstance(val, int) and not (1 <= val <= 65535):\n            raise ValueError(f'port 超出范围: {val}')\n    return config"
        )]},
        "A6": {"patches": [(
            "        # A6: 重复键静默后者胜（不报错）\n        target[key] = _convert(val)             # A3: 类型错",
            "        if key in target:  # A6 修复：重复键报错\n            raise ValueError(f\"重复键: {key}\")\n        target[key] = _convert(val)"
        )]},
    },

    "t3-scheduler": {
        "P1": {"patches": [(
            "        tasks_sorted = sorted(tasks, key=lambda t: t[1], reverse=False)",
            "        tasks_sorted = sorted(tasks, key=lambda t: t[1], reverse=True)"
        )]},
        "P2": {"patches": [(
            "            # P2: 配额边界 off-by-one（=quota 时也拒绝，末位发不出）\n            if self.used + units >= self.quota:",
            "            # P2 修复：允许恰好用满配额\n            if self.used + units > self.quota:"
        )]},
        "P3": {"patches": [(
            "    def execute_idempotent(self, tid):\n        \"\"\"P3: 应幂等（同 id 只执行一次），实际每次重复执行。\"\"\"\n        self._exec_count[tid] = self._exec_count.get(tid, 0) + 1\n        self.results[tid] = f\"done-{tid}\"",
            "    def execute_idempotent(self, tid):\n        \"\"\"P3 修复：同 id 只执行一次。\"\"\"\n        if tid in self._idempotent:\n            return\n        self._idempotent.add(tid)\n        self._exec_count[tid] = self._exec_count.get(tid, 0) + 1\n        self.results[tid] = f\"done-{tid}\""
        )]},
        "P4": {"patches": [(
            "        prev = self.used\n        time.sleep(0.001)               # 模拟处理耗时（放大竞态窗口）\n        self.used = prev + units\n        self.results[tid] = f\"done-{tid}\"\n        self.executed.append(tid)",
            "        with self.lock:  # P4 修复：used 更新加锁\n            prev = self.used\n            time.sleep(0.001)               # 模拟处理耗时\n            self.used = prev + units\n            self.results[tid] = f\"done-{tid}\"\n            self.executed.append(tid)"
        )]},
        "P5": {"patches": [(
            "            # P5: 无老化/晋升——低于 min_priority 的任务永久丢弃（饥饿）\n            if prio < self.min_priority:\n                continue",
            "            # P5 修复：老化——低优先级提升（不丢弃）\n            if prio < self.min_priority:\n                prio = self.min_priority"
        )]},
        "P6": {"patches": [(
            "    def retry(self, tid, attempt):\n        \"\"\"P6: 重试无退避（应指数退避，attempt 大时延迟增长）。\"\"\"\n        # P6: 无退避——立即重试（风暴）\n        return f\"retry-{tid}-{attempt}\"",
            "    def retry(self, tid, attempt):\n        \"\"\"P6 修复：指数退避。\"\"\"\n        delay = min(0.05 * attempt, 0.5)\n        time.sleep(delay)\n        return f\"retry-{tid}-{attempt}\""
        )]},
        "P7": {"pre": ["P1"], "patches": [(
            "        # P7: 完成记录按提交顺序（应反映实际执行完成顺序）\n        self.finished = [t[0] for t in tasks]",
            "        self.finished = []  # P7 修复：执行后按完成顺序记录"
        ), (
            "            self._dispatch(tid, units)",
            "            self._dispatch(tid, units)\n        self.finished = list(self.executed)  # P7 修复"
        )]},
    },

    "t4-statemachine": {
        "S1": {"patches": [(
            "    def transition(self, to):\n        # S1: 不查合法性表——DRAFT 可直接跳到 ARCHIVED 等非法目标\n        self.state = to\n        return True",
            "    def transition(self, to):\n        # S1 修复：查合法性表\n        if to in VALID_TRANSITIONS.get(self.state, set()):\n            self.state = to\n            return True\n        return False"
        )]},
        "S2": {"patches": [(
            "        # S2: 错序——archiver 排在 validator 前（读未写入的 checksum）\n        self.tx.add(\"archiver\", lambda: self._archiver(doc),\n                    undo=lambda: self.archives and self.archives.pop())\n        self.tx.add(\"validator\", lambda: self._validator(doc),\n                    undo=lambda: setattr(self, \"checksum\", None))",
            "        # S2 修复：validator 先于 archiver\n        self.tx.add(\"validator\", lambda: self._validator(doc),\n                    undo=lambda: setattr(self, \"checksum\", None))\n        self.tx.add(\"archiver\", lambda: self._archiver(doc),\n                    undo=lambda: self.archives and self.archives.pop())"
        )]},
        "S3": {"pre": ["S2"], "patches": [(
            "    def run(self):\n        # S3: 逐步执行，任一步失败异常外泄——不回滚已成功步骤（部分提交）\n        for s in self._steps:\n            s[\"do\"]()\n        return True",
            "    def run(self):\n        # S3 修复：任一步失败，只回滚已执行步骤（原子性）\n        done = 0\n        try:\n            for s in self._steps:\n                s[\"do\"]()\n                done += 1\n        except Exception:\n            for s in reversed(self._steps[:done]):\n                if s[\"undo\"]:\n                    s[\"undo\"]()\n            raise\n        return True"
        )]},
        "S4": {"patches": [(
            "        self.tx.add(\"notifier\", lambda: self._notifier(doc), undo=None)   # S4",
            "        self.tx.add(\"notifier\", lambda: self._notifier(doc),\n                    undo=lambda: self.notified.pop())  # S4 修复"
        )]},
        "S5": {"patches": [(
            "        # S5: 只通知前 N-1 个订阅者——最后一个永远收不到\n        for fn in self._subs[:-1]:",
            "        # S5 修复：通知所有订阅者\n        for fn in self._subs:"
        )]},
        "S6": {"patches": [(
            "import time\n\nVALID_TRANSITIONS = {",
            "import threading\nimport time\n\n_SM_LOCK = threading.Lock()\n\nVALID_TRANSITIONS = {"
        ), (
            "    def cas(self, expected, to):\n        # S6: 检查与更新非原子（ABA 竞态窗口）\n        if self.state == expected:\n            time.sleep(0.001)   # 竞态窗口（模拟处理耗时）\n            self.state = to\n            return True\n        return False",
            "    def cas(self, expected, to):\n        # S6 修复：检查与更新原子\n        with _SM_LOCK:\n            if self.state == expected:\n                time.sleep(0.001)\n                self.state = to\n                return True\n        return False"
        )]},
        "S7": {"patches": [(
            "        # S3: tx.run 失败异常外泄——部分提交残留（应 try/except + rollback）\n        self.tx.run()\n        self.sm.transition(\"PUBLISHED\")",
            "        # S7 修复：validator 超时 → 标记 FAILED 不卡死\n        try:\n            self.tx.run()\n        except TimeoutError:\n            self.sm.transition(\"FAILED\")\n            raise\n        self.sm.transition(\"PUBLISHED\")"
        )]},
    },

    "t5-renderer": {
        "R1": {"patches": [(
            "        # R1: 转义漏注——HTML 特殊字符原样输出（注入）\n        if node[\"kind\"] == \"h1\":",
            "        # R1 修复：HTML 转义\n        cleaned = cleaned.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')\n        if node[\"kind\"] == \"h1\":"
        )]},
        "R2": {"patches": [(
            "        children = []\n        for kind, content in tokens:\n            if kind == \"li\":\n                # R2: 列表项不分组到 <ul>——挂错父节点（嵌套结构错）\n                children.append({\"kind\": \"li\", \"content\": content})\n            else:\n                children.append({\"kind\": kind, \"content\": content})\n        return children",
            "        children = []\n        pending = []\n        for kind, content in tokens:\n            if kind == \"li\":\n                pending.append({\"kind\": \"li\", \"content\": content})\n            else:\n                if pending:\n                    children.append({\"kind\": \"ul\", \"children\": pending})\n                    pending = []\n                children.append({\"kind\": kind, \"content\": content})\n        if pending:\n            children.append({\"kind\": \"ul\", \"children\": pending})\n        return children"
        ), (
            "    def _render_node(self, node):\n        # R5: 每次渲染分配资源且不释放（泄漏）\n        self._allocated.append(object())\n        content = node[\"content\"]",
            "    def _render_node(self, node):\n        # R5: 每次渲染分配资源且不释放（泄漏）\n        self._allocated.append(object())\n        if node[\"kind\"] == \"ul\":  # R2 修复：渲染列表容器\n            inner = \"\".join(self._render_node(c) for c in node[\"children\"])\n            return f\"<ul>{inner}</ul>\"\n        content = node[\"content\"]"
        )]},
        "R3": {"patches": [(
            "        # R3: 渲染顺序反了（兄弟节点逆序输出）\n        for node in reversed(nodes):",
            "        # R3 修复：按文档顺序渲染\n        for node in nodes:"
        )]},
        "R4": {"patches": [(
            "        # R4: 布局溢出未处理——超长内容原样输出（不截断/收缩）\n        return f\"<p>{cleaned}</p>\"",
            "        # R4 修复：超长内容截断\n        if len(cleaned) > 1000:\n            cleaned = cleaned[:1000] + \"…\"\n        return f\"<p>{cleaned}</p>\""
        )]},
        "R5": {"patches": [(
            "        # R5: 每次渲染分配资源且不释放（泄漏）\n        self._allocated.append(object())",
            "        # R5 修复：渲染后释放\n        self._allocated.append(object())\n        self._allocated.pop()"
        )]},
        "R6": {"patches": [(
            "    def render_file(self, path):\n        # R6: 缓存按路径——文件内容变更后仍返回旧渲染\n        if path in self.cache:\n            return self.cache[path]\n        text = Path(path).read_text(encoding=\"utf-8\")\n        out = self.render(text)\n        self.cache[path] = out\n        return out",
            "    def render_file(self, path):\n        # R6 修复：按内容校验缓存\n        text = Path(path).read_text(encoding=\"utf-8\")\n        if path in self.cache and self.cache[path][0] == text:\n            return self.cache[path][1]\n        out = self.render(text)\n        self.cache[path] = (text, out)\n        return out"
        )]},
        "R7": {"patches": [(
            "        # R7: 编码错——非 ASCII 字符替换为 ?（乱码）\n        cleaned = content.encode(\"ascii\", \"replace\").decode(\"ascii\")",
            "        # R7 修复：保持 UTF-8 编码\n        cleaned = content"
        )]},
        "R8": {"patches": [(
            "        # R8: 海量行输入不处理（token 过多时崩溃）\n        if len(tokens) > 5000:\n            raise MemoryError(\"输入过大: token 数超限\")",
            "        # R8 修复：超大输入截断（不崩）\n        if len(tokens) > 5000:\n            tokens = tokens[:5000]"
        )]},
    },
}


def apply_patch(text, patches):
    for old, new in patches:
        if old not in text:
            raise AssertionError(f"patch 锚点未找到: {old[:70]!r}")
        text = text.replace(old, new, 1)
    return text


def copy_task(task_id):
    src = TASKS / task_id
    dst = Path(tempfile.mkdtemp(prefix=f"audit-{task_id}-")) / task_id
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return dst


def run_pytest(task_dir):
    r = subprocess.run([sys.executable, "-m", "pytest", "tests/test_biz.py", "-q", "--no-header"],
                       cwd=task_dir, capture_output=True, text=True, timeout=120)
    failed = set()
    for line in r.stdout.splitlines():
        line = line.strip()
        if line.startswith("FAILED "):
            failed.add(line.split()[1].split("::")[-1])
    return failed


def apply_bugs(task_dir, task_id, bug_ids):
    """把 task 下 src 里所有文本文件按补丁替换（匹配才替换，补丁可跨文件）。
    bug_ids 为空表示不修。"""
    for src in (TASKS / task_id / "src").iterdir():
        if src.suffix != ".py":
            continue
        text = src.read_text(encoding="utf-8")
        for bid in bug_ids:
            for old, new in FIXES[task_id][bid]["patches"]:
                if old in text:
                    text = text.replace(old, new, 1)
        (task_dir / "src" / src.name).write_text(text, encoding="utf-8")


def precheck_anchors():
    """启动预检：所有补丁锚点必须存在于某个 src 文件（防笔误静默跳过）。"""
    missing = []
    for task_id, bugs in FIXES.items():
        texts = [p.read_text(encoding="utf-8")
                 for p in (TASKS / task_id / "src").glob("*.py")]
        for bid, spec in bugs.items():
            for old, _ in spec["patches"]:
                if not any(old in t for t in texts):
                    missing.append(f"{task_id}/{bid}: {old[:60]!r}")
    if missing:
        print("锚点预检失败，以下补丁在源码中不存在:")
        for m in missing:
            print("  " + m)
        sys.exit(2)


def main():
    precheck_anchors()
    report = []
    total_bugs = 0
    ok_bugs = 0

    for task_id, bugs in FIXES.items():
        report.append(f"\n## {task_id}")

        # 基准失败集（全部 bug 存在）
        base = copy_task(task_id)
        baseline = run_pytest(base)
        report.append(f"  基准业务失败 {len(baseline)}: {sorted(baseline)}")

        for bug_id, spec in bugs.items():
            total_bugs += 1
            pre = spec.get("pre", [])
            try:
                if not pre:
                    # 直接 bug：单独修复 → 失败集变小
                    tmp = copy_task(task_id)
                    apply_bugs(tmp, task_id, [bug_id])
                    after = run_pytest(tmp)
                    shutil.rmtree(tmp.parent)
                    gone = baseline - after
                    if gone:
                        report.append(f"  {bug_id}: ✅ 修复后 {len(gone)} 测试变绿 {sorted(gone)}")
                        ok_bugs += 1
                    else:
                        report.append(f"  {bug_id}: ❌ 修复后无测试变绿（bug 未生效?）")
                else:
                    # 被掩盖 bug：先修 pre → 专属仍红（独立挡着）；修 pre+本 bug → 变绿
                    tmp = copy_task(task_id)
                    apply_bugs(tmp, task_id, pre)
                    after_pre = run_pytest(tmp)
                    shutil.rmtree(tmp.parent)

                    tmp2 = copy_task(task_id)
                    apply_bugs(tmp2, task_id, pre + [bug_id])
                    after_both = run_pytest(tmp2)
                    shutil.rmtree(tmp2.parent)

                    still_blocked = after_pre - after_both  # 修 pre 后仍红的 = 本 bug 挡的
                    gone = after_pre - after_both
                    if gone:
                        report.append(f"  {bug_id}: ✅ 被掩盖 bug——修 {pre} 后专属仍红（{sorted(after_pre)}），再修本 bug {len(gone)} 测试变绿 {sorted(gone)}")
                        ok_bugs += 1
                    else:
                        report.append(f"  {bug_id}: ❌ 修 pre 后已绿或本 bug 无独立影响")
            except AssertionError as e:
                report.append(f"  {bug_id}: ❌ {e}")
            except Exception as e:
                report.append(f"  {bug_id}: ❌ 异常 {e}")

        shutil.rmtree(base.parent)

    report.insert(0, f"# 逐 bug 审计结果：{ok_bugs}/{total_bugs} 个 bug 确认真实生效")
    print("\n".join(report))
    return 0 if ok_bugs == total_bugs else 1


if __name__ == "__main__":
    sys.exit(main())

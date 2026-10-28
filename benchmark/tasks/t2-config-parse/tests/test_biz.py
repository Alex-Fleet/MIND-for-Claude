"""业务测试：修完 6 个耦合 bug 后全部通过（网状，见设计文档 T2）。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from run import load_config

def test_quoted_value():  # A1 引号（修复后验证）
    r = load_config('name="hello world"\n')
    assert r["name"] == "hello world"

def test_escaped_value():  # A1 转义（\\ 未处理 → 暴露）
    r = load_config('path="C:\\\\tmp"\n')
    assert r["path"] == "C:\\tmp"

def test_nested_section():  # A2 浅层嵌套（修复后验证）
    r = load_config("[db.host]\nuser=admin\n")
    assert r["db"]["host"]["user"] == "admin"

def test_deep_nested():  # A2 深层嵌套不崩（递归爆栈 → 暴露）
    N = 1200
    deep = ".".join(f"s{i}" for i in range(N))
    r = load_config(f"[{deep}]\nk=v\n")
    node = r
    for i in range(N):
        node = node[f"s{i}"]
    assert node["k"] == "v"

def test_type_conversion():  # A3 类型转换（bool 判反 → 暴露）
    r = load_config("port=8080\nenabled=true\nverbose=false\n")
    assert r["port"] == 8080 and r["enabled"] is True and r["verbose"] is False

def test_defaults_not_override():  # A4 默认不覆盖用户值
    r = load_config("timeout=30\n", defaults={"timeout": 10, "retries": 3})
    assert r["timeout"] == 30 and r["retries"] == 3

def test_invalid_rejected():  # A5 非法值被拒（校验漏项 → 暴露）
    try:
        cfg = load_config("port=99999\n")
        assert cfg["port"] != 99999, f"非法端口应被拦截，实际保留 {cfg['port']}"
    except ValueError:
        pass

def test_defaults_do_not_hide_invalid():  # A4 掩盖 A5：默认值洗白非法输入
    # 全部 bug 存在时此测试通过（非法值被默认替换，看似没问题）
    # 修 A4（用户值优先）后：用户非法值保留 → A5 校验漏项浮出
    try:
        cfg = load_config("port=99999\n", defaults={"port": 8080})
        assert cfg["port"] != 99999, "用户显式非法值不应被默认洗白"
    except ValueError:
        pass

def test_duplicate_key_error():  # A6 重复键应报错
    raised = False
    try:
        load_config("a=1\na=2\n")
    except Exception:
        raised = True
    assert raised, "重复键应报错"

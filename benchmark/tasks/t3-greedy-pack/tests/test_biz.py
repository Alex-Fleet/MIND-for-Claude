"""业务测试：按字符数（非字节）打包。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from packer import pack, MAX_CHARS

def test_three_files_total_exactly_max():
    # 4000中文(3字节/字) + 4000中文 + 2000 ASCII = 10000 字符（=MAX），应 1 包
    # bug(字节): 26000 字节 → 被拆成 3 包
    files = [("c1.txt", "字"*4000), ("c2.txt", "字"*4000), ("a.txt", "a"*2000)]
    assert sum(len(c) for _, c in files) == MAX_CHARS
    packs = pack(files)
    assert len(packs) == 1, f"总 {MAX_CHARS} 字符应一个包，实际 {len(packs)} 包"

def test_chinese_files_share_pack():
    # 两个 4000 中文 = 8000 字符，应 1 包
    files = [("x.txt", "字"*4000), ("y.txt", "字"*4000)]
    packs = pack(files)
    assert len(packs) == 1, "两个中文文件（8000字符）应共享一包"

def test_mixed_chinese_ascii():
    # 2000 汉字 + 4000 ASCII = 6000 字符，应 1 包（bug 字节: 6000+4000=10000? 汉字6000字节+4000=10000 恰卡）
    files = [("mix.txt", "字"*2000 + "a"*4000)]
    packs = pack(files)
    assert len(packs) == 1, "中英混排 6000 字符应一个包"

def test_ascii_fits_exactly():
    content = "a" * MAX_CHARS
    packs = pack([("a.txt", content)])
    assert len(packs) == 1

def test_mixed_within_limit():
    # 1000 中文 + 5000 ASCII = 6000 字符，应 1 包
    files = [("cn.txt", "字"*1000), ("en.txt", "b"*5000)]
    assert sum(len(c) for _, c in files) == 6000
    packs = pack(files)
    assert len(packs) == 1

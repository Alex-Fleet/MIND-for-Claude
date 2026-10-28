"""LLM 输出解析器 — 把模型返回的文本转成 dict。

LLM 经常输出: ```json 代码块包裹、尾逗号、单引号、混合引号、前后解释文字、
多行、注释 等。本解析器对这类常见畸形做容错，同时保持标准 JSON 的解析行为。

容错清单:
- ```json 代码块包裹
- 前后夹解释文字（自动定位第一个可解析的 JSON 值）
- 尾逗号 / 多余逗号（对象与数组）
- 单引号 / 混合引号（字符串与键）
- 多行
- // 行注释、/* */ 块注释
"""
import json
import re

# 数字: -?(0|[1-9]\d*)(\.\d+)?([eE][+-]?\d+)?
_NUMBER_RE = re.compile(r"-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?")

_WS = " \t\n\r"
_ESCAPES = {
    '"': '"', "'": "'", "\\": "\\", "/": "/",
    "b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t",
}
# 单引号字符串中，紧跟 ' 之后若属于这些字符，才视为字符串结束；
# 否则把该 ' 当作字符串内部的撇号（如 it's）按字面处理
_SINGLE_QUOTE_END = set(",}] \t\n\r:")

class _Parser:
    """带位置游标的容错 JSON 递归下降解析器。"""

    __slots__ = ("text", "i")

    def __init__(self, text, i=0):
        self.text = text
        self.i = i

def parse(text: str) -> dict:
    """解析 LLM 输出的 JSON 文本为 dict。失败抛 ValueError。"""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("empty input")

    t = _strip_codeblock(text.strip())
    if not t:
        raise ValueError("empty input")

    if t[0] in "{[":
        # 对象/数组直接走容错解析（含尾逗号、单引号等）
        try:
            return _parse_value(_Parser(t))
        except ValueError:
            # 开头 {/[ 可能属于解释文字（如 {说明} {"a": 1}）：
            # 退回到"定位第一个可解析的 JSON 值"
            return _extract_first_value(t)

    # 标准 JSON 标量（数字/字符串/true/false/null）保持原行为
    try:
        return json.loads(t)
    except ValueError:
        pass

    # 前后夹解释文字：定位第一个可解析的 JSON 值
    return _extract_first_value(t)

# 单行代码块开头的围栏（```json / ``` 等，可带语言标识与空白）
_FENCE_OPEN_RE = re.compile(r"^```[a-zA-Z0-9_+.-]*\s*")

def _strip_codeblock(t: str) -> str:
    """剥掉 ```json 代码块围栏（支持多行与单行形式）。"""
    if not t.startswith("```"):
        return t
    lines = t.splitlines()
    if not lines:
        return ""
    if len(lines) == 1:
        # 单行形式如 ```json {"a": 1}```：仅剥首尾围栏，
        # 不用 (.*?) 惰性匹配，避免字符串内容里的 ``` 被误当闭合围栏
        body = _FENCE_OPEN_RE.sub("", lines[0])
        body = re.sub(r"```\s*$", "", body)
        return body.strip()
    # 多行形式：去掉首行围栏与末行围栏
    lines = lines[1:] if lines[0].startswith("```") else lines
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()

def _extract_first_value(t: str) -> object:
    """在夹杂解释文字的文本中定位第一个可解析的 JSON 值。"""
    candidates = [i for i, c in enumerate(t) if c in "{["]
    if not candidates:
        raise ValueError("no JSON value found")
    last_err = None
    for idx in candidates:
        try:
            return _parse_value(_Parser(t, idx))
        except ValueError as e:
            last_err = e
    raise last_err

def _skip_ws(p: _Parser) -> None:
    """跳过空白、// 行注释、/* */ 块注释。"""
    text, n = p.text, len(p.text)
    while p.i < n:
        c = text[p.i]
        if c in _WS:
            p.i += 1
        elif text.startswith("//", p.i):
            p.i += 2
            while p.i < n and text[p.i] not in "\n\r":
                p.i += 1
        elif text.startswith("/*", p.i):
            end = text.find("*/", p.i + 2)
            p.i = n if end == -1 else end + 2  # 未闭合的块注释按注释到结尾处理
        else:
            break

def _parse_value(p: _Parser) -> object:
    _skip_ws(p)
    if p.i >= len(p.text):
        raise ValueError("unexpected end of input")
    c = p.text[p.i]
    if c == "{":
        return _parse_object(p)
    if c == "[":
        return _parse_array(p)
    if c in "\"'":
        return _parse_string(p)
    for kw, val in (("true", True), ("false", False), ("null", None)):
        if p.text.startswith(kw, p.i):
            nxt = p.text[p.i + len(kw)] if p.i + len(kw) < len(p.text) else ""
            if not nxt.isalnum() and nxt != "_":
                p.i += len(kw)
                return val
    if c == "-" or c.isdigit():
        return _parse_number(p)
    raise ValueError(f"unexpected character {c!r} at position {p.i}")

def _parse_object(p: _Parser) -> dict:
    p.i += 1  # '{'
    result = {}
    while True:
        _skip_ws(p)
        if p.i >= len(p.text):
            raise ValueError("unterminated object")
        c = p.text[p.i]
        if c == ",":  # 容忍多余/前导逗号
            p.i += 1
            continue
        if c == "}":  # 空对象或尾逗号后的收尾
            p.i += 1
            return result
        if c in "\"'":
            key = _parse_string(p)
        else:
            # 无引号键容错（LLM 常输出 {a: 1} 这种）
            key = _parse_unquoted_key(p)
        _skip_ws(p)
        if p.i >= len(p.text) or p.text[p.i] != ":":
            raise ValueError(f"expected ':' after key at position {p.i}")
        p.i += 1
        result[key] = _parse_value(p)
        _skip_ws(p)
        if p.i >= len(p.text):
            raise ValueError("unterminated object")
        c = p.text[p.i]
        if c == ",":
            p.i += 1
            continue
        if c == "}":
            p.i += 1
            return result
        raise ValueError(f"expected ',' or '}}' at position {p.i}")

def _parse_array(p: _Parser) -> list:
    p.i += 1  # '['
    result = []
    while True:
        _skip_ws(p)
        if p.i >= len(p.text):
            raise ValueError("unterminated array")
        c = p.text[p.i]
        if c == ",":  # 容忍多余/前导逗号
            p.i += 1
            continue
        if c == "]":  # 空数组或尾逗号后的收尾
            p.i += 1
            return result
        result.append(_parse_value(p))
        _skip_ws(p)
        if p.i >= len(p.text):
            raise ValueError("unterminated array")
        c = p.text[p.i]
        if c == ",":
            p.i += 1
            continue
        if c == "]":
            p.i += 1
            return result
        raise ValueError(f"expected ',' or ']' at position {p.i}")

def _parse_unquoted_key(p: _Parser) -> str:
    """解析无引号键：收集非空白、非分隔符字符直到冒号/分隔符。"""
    start = p.i
    text, n = p.text, len(p.text)
    while p.i < n:
        c = text[p.i]
        if c in _WS or c in ",:{}[]\"'":
            break
        p.i += 1
    if p.i == start:
        raise ValueError(f"empty key at position {start}")
    return text[start:p.i]

def _parse_string(p: _Parser) -> str:
    quote = p.text[p.i]
    p.i += 1
    out = []
    n = len(p.text)
    while p.i < n:
        c = p.text[p.i]
        if c == "\\":
            p.i += 1
            if p.i >= n:
                raise ValueError("unterminated escape")
            e = p.text[p.i]
            if e == "u":
                hex4 = p.text[p.i + 1 : p.i + 5]
                if len(hex4) != 4:
                    raise ValueError("bad \\u escape")
                try:
                    out.append(chr(int(hex4, 16)))
                except ValueError:
                    raise ValueError("bad \\u escape") from None
                p.i += 4
            else:
                out.append(_ESCAPES.get(e, e))  # 未知转义原样保留
            p.i += 1
        elif c == quote:
            if quote == "'" and p.i + 1 < n and p.text[p.i + 1] not in _SINGLE_QUOTE_END:
                # 单引号字符串内部的撇号（如 it's）按字面处理
                out.append("'")
                p.i += 1
                continue
            p.i += 1
            return "".join(out)
        else:
            out.append(c)
            p.i += 1
    raise ValueError("unterminated string")

def _parse_number(p: _Parser) -> object:
    m = _NUMBER_RE.match(p.text, p.i)
    if not m:
        raise ValueError(f"invalid number at position {p.i}")
    s = m.group(0)
    p.i = m.end()
    if "." in s or "e" in s or "E" in s:
        return float(s)
    return int(s)

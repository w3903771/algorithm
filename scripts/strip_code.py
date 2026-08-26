"""提交前剥掉注释与文档字符串，只交可执行代码。

本仓库的题解文档字符串是**教程正文**——站点会把它渲染成「一句话 + 解题思路 +
复杂度」那几节，动辄十几行中文。那是给读者看的，不该跟着代码进判题机。
注释同理：写给维护者的推导过程，判题机不需要。

实现上用 `tokenize` 定位注释、用 `ast` 定位文档字符串，**不用正则**——
`s = "abc # not a comment"` 这种字符串里的 `#` 正则分不出来，剥错就是一次
莫名其妙的 WA。剥完还会 `compile()` 校验一遍，编译不过就退回原文，
宁可多交几行注释，也不能交出一份跑不了的代码。

顺带去掉 `from __future__ import ...`：**力扣会在提交的代码前面拼自己的前导代码**，
于是 future 导入永远不在文件第一行，一提交就是
`SyntaxError: from __future__ imports must occur at the beginning of the file`
（实测踩过）。仓库里的题解骨架因此也不用 future 导入，节点类型的注解一律加引号。
"""
from __future__ import annotations

import ast
import io
import re
import tokenize


# 力扣会在提交的代码前拼前导代码，future 导入不可能保持在首行，必然 SyntaxError
_FUTURE = re.compile(r"^\s*from\s+__future__\s+import\s")


def _comment_spans(src: str) -> dict:
    """行号 -> 该行注释起始列。tokenize 认得字符串字面量，不会误判其中的 `#`。"""
    spans = {}
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT:
                row, col = tok.start
                spans.setdefault(row, col)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return {}
    return spans


def _docstring_spans(src: str) -> tuple:
    """文档字符串的行区间。

    返回 (要删除的区间, 删掉后会变空的块的区间)。后者不能直接删——
    函数体空了就是语法错误，得原地换成 `pass`。
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return [], []
    drop, lonely = [], []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                 ast.AsyncFunctionDef)):
            continue
        body = getattr(node, "body", None) or []
        if not body:
            continue
        first = body[0]
        if not (isinstance(first, ast.Expr)
                and isinstance(getattr(first, "value", None), ast.Constant)
                and isinstance(first.value.value, str)):
            continue
        span = (first.lineno, getattr(first, "end_lineno", first.lineno))
        # 模块级文档字符串删光没关系；函数/类体只剩它一句时得留个 pass
        if len(body) == 1 and not isinstance(node, ast.Module):
            lonely.append((span, first.col_offset))
        else:
            drop.append(span)
    return drop, lonely


def strip(src: str) -> str:
    """剥掉注释与文档字符串。剥完编译不过就原样返回。"""
    lines = src.replace("\r\n", "\n").split("\n")
    comments = _comment_spans(src)
    drop, lonely = _docstring_spans(src)

    kill = set()
    for lo, hi in drop:
        kill.update(range(lo, hi + 1))
    replace = {}
    for (lo, hi), col in lonely:
        kill.update(range(lo, hi + 1))
        replace[lo] = " " * col + "pass"

    out = []
    for i, line in enumerate(lines, 1):
        if i in replace:
            out.append(replace[i])
            continue
        if i in kill:
            continue
        if i in comments:
            line = line[:comments[i]].rstrip()
            if not line:                 # 整行都是注释
                continue
        if _FUTURE.match(line):
            continue
        out.append(line.rstrip())

    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"

    try:
        compile(text, "<stripped>", "exec")
    except SyntaxError:
        return src                       # 剥坏了就退回原文，绝不交出跑不了的代码
    return text


def summary(src: str, stripped: str) -> str:
    a, b = len(src.split("\n")), len(stripped.split("\n"))
    return f"{a}->{b} 行"

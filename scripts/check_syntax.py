#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""全库 Python 源码的语法闸门：**用运行本脚本的解释器版本去解析**。

    uv run python scripts/check_syntax.py          # 全部
    uv run python scripts/check_syntax.py --list   # 顺便列出扫了哪些目录

为什么需要它（教训十六 / 十八）：正文与附录反复承诺「全书代码一律兼容 3.9」
（`docs/appendix/b2-python-templates.md` 开篇那句），而**没有任何闸门在看这件事**。
`verify.py` 会跑题解，但它跑的是本地解释器——本地恰好是 3.9 时它顺带验到了，
换一台机器就验不到；CI 那边原先跑 3.11，写了 `match` / `int | None` 也照样全绿。

**不用 `compileall`**：它会往每个题目录里撒 `__pycache__`，而 `solutions/**` 被
`.gitignore` 盖着，`git status` 看不见——正是 09 教训十三点名的那类副作用
（P-M③ 锁定复核就被这个咬过一次）。`ast.parse` 只解析不写盘。

**它看不见什么**：只查**语法**，不查运行时 API。`str.removeprefix()`（3.9 起）
或 `itertools.pairwise`（3.10 起）这类是合法语法、导入才报错，
要靠 `verify.py` 真跑一遍才抓得到。
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCAN = ("solutions", "scripts", "hooks")


def main(argv: list) -> int:
    bad, n = [], 0
    for d in SCAN:
        for f in sorted((ROOT / d).rglob("*.py")):
            if "__pycache__" in f.parts:
                continue
            n += 1
            try:
                ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
            except SyntaxError as e:
                bad.append((f.relative_to(ROOT).as_posix(), e.lineno, e.msg))

    v = "%d.%d.%d" % sys.version_info[:3]
    if "--list" in argv:
        print("扫描目录：" + " · ".join(SCAN))
    for rel, ln, msg in bad:
        print("[语法] %s:%s  %s" % (rel, ln, msg))
    print("\nPython %s 解析 %d 份源码：通过 %d、失败 %d"
          % (v, n, n - len(bad), len(bad)))
    if bad:
        print("本仓库承诺「全书代码兼容 Python 3.9」——"
              "要么改写成 3.9 能解析的形式，要么改掉那句承诺。")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

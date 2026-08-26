"""BISHI27 构造数对 —— special judge。

校验：
  - 输出 -1 时，暴力确认确实无解；
  - 输出 (a, b) 时，逐条检查 1<=a,b<=x、b|a、a*b>x、a/b<x。
"""


def _exists(x: int) -> bool:
    for b in range(1, x + 1):
        for a in range(b, x + 1, b):
            if a * b > x and a // b < x:
                return True
    return False


def check(inp: str, out: str) -> bool:
    x = int(inp.split()[0])
    toks = out.split()
    if not toks:
        return False
    try:
        vals = [int(v) for v in toks]
    except ValueError:
        return False
    if len(vals) == 1:
        return vals[0] == -1 and not _exists(x)
    if len(vals) != 2:
        return False
    a, b = vals
    if not (1 <= a <= x and 1 <= b <= x):
        return False
    if a % b != 0:
        return False
    return a * b > x and a // b < x

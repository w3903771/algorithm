"""BISHI37 数位差与数值和的构造 —— special judge。

校验每组：x, y 非负、x + y == n，且 |digitsum(x) - digitsum(y)| <= 1。
"""


def _ds(v: int) -> int:
    s = 0
    while v:
        s += v % 10
        v //= 10
    return s


def check(inp: str, out: str) -> bool:
    toks = inp.split()
    t = int(toks[0])
    ns = [int(v) for v in toks[1:1 + t]]
    ans = out.split()
    if len(ans) != 2 * t:
        return False
    for i, n in enumerate(ns):
        try:
            x = int(ans[2 * i])
            y = int(ans[2 * i + 1])
        except ValueError:
            return False
        if x < 0 or y < 0 or x + y != n:
            return False
        if abs(_ds(x) - _ds(y)) > 1:
            return False
    return True

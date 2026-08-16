"""BISHI28 构造数独 —— special judge。

校验：n*n 个非负整数，每一行的和、每一列的和都等于 k。
（本题恒有解，所以输出 -1 一律判错。）
"""


def check(inp: str, out: str) -> bool:
    n, k = map(int, inp.split()[:2])
    toks = out.split()
    if len(toks) != n * n:
        return False
    try:
        vals = [int(v) for v in toks]
    except ValueError:
        return False
    if any(v < 0 for v in vals):
        return False
    for i in range(n):
        if sum(vals[i * n:(i + 1) * n]) != k:
            return False
    for j in range(n):
        if sum(vals[j::n]) != k:
            return False
    return True

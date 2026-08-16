"""BISHI40 数组取精 —— special judge。

校验：
  - 输出的 k 与下标个数一致，下标互异且在 [1, n] 内；
  - k <= floor(n/2) + 1；
  - 2 * Σ_{i∈P} a_i > Σ a  且  2 * Σ_{i∈P} b_i > Σ b（严格过半）。
"""


def check(inp: str, out: str) -> bool:
    toks = inp.split()
    n = int(toks[0])
    a = [int(v) for v in toks[1:1 + n]]
    b = [int(v) for v in toks[1 + n:1 + 2 * n]]

    o = out.split()
    if not o:
        return False
    try:
        k = int(o[0])
        idx = [int(v) for v in o[1:]]
    except ValueError:
        return False
    if k != len(idx) or k <= 0:
        return False
    if k > n // 2 + 1:
        return False
    if len(set(idx)) != k:
        return False
    if any(p < 1 or p > n for p in idx):
        return False
    sa = sum(a[p - 1] for p in idx)
    sb = sum(b[p - 1] for p in idx)
    return 2 * sa > sum(a) and 2 * sb > sum(b)

"""BISHI29 小红的排列构造① —— special judge。

校验：
  - n <= 2 必须输出 -1（这两种情况确实无解）；
  - 否则输出必须是 1..n 的排列，且每个 a_i + i 都不是质数。
"""


def check(inp: str, out: str) -> bool:
    n = int(inp.split()[0])
    toks = out.split()
    try:
        vals = [int(v) for v in toks]
    except ValueError:
        return False
    if n <= 2:
        return vals == [-1]
    if len(vals) != n:
        return False
    if sorted(vals) != list(range(1, n + 1)):
        return False

    # a_i + i 最大为 2n，线性筛出 [0, 2n] 的合数标记
    m = 2 * n
    is_comp = bytearray(m + 1)
    is_comp[0] = is_comp[1] = 1          # 0 和 1 都不是质数
    p = 2
    while p * p <= m:
        if not is_comp[p]:
            start = p * p
            is_comp[start::p] = b"\x01" * len(range(start, m + 1, p))
        p += 1
    for i, v in enumerate(vals, 1):
        if not is_comp[v + i]:           # 不是合数也不是 0/1 -> 是质数
            return False
    return True

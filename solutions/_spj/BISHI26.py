"""BISHI26 构造C的歪 —— special judge。

校验：输出的 c 与输入的 a、b 排序后必须构成等差数列（x + z == 2y）。
"""


def check(inp: str, out: str) -> bool:
    a, b = map(int, inp.split()[:2])
    toks = out.split()
    if len(toks) != 1:
        return False
    try:
        c = int(toks[0])
    except ValueError:
        return False
    x, y, z = sorted((a, b, c))
    return x + z == 2 * y

"""PIO18 校验器：n 个正整数且和为 m 即可。"""


def check(inp: str, out: str) -> bool:
    n, m = map(int, inp.split()[:2])
    vals = out.split()
    if len(vals) != n:
        return False
    try:
        nums = [int(v) for v in vals]
    except ValueError:
        return False
    return all(v >= 1 for v in nums) and sum(nums) == m

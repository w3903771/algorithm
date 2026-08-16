"""BISHI32 被打乱的异或和 —— special judge。

合法条件：x 必须是数组里出现过的某个元素，且删掉它一个之后，
剩余 n-1 个数的异或等于 x（等价于「x 在数组中出现」+「全体异或为 0」）。
校验器直接按定义逐组验证。
"""


def check(inp: str, out: str) -> bool:
    it = iter(inp.split())
    try:
        t = int(next(it))
    except StopIteration:
        return False
    ans = out.split()
    if len(ans) != t:
        return False
    for idx in range(t):
        n = int(next(it))
        a = [int(next(it)) for _ in range(n)]
        try:
            x = int(ans[idx])
        except ValueError:
            return False
        if x not in a:
            return False
        rest = a[:]
        rest.remove(x)                # 只删掉一个出现
        r = 0
        for v in rest:
            r ^= v
        if r != x:
            return False
    return True

"""BM19 寻找峰值 —— 特判校验器。

题面原文：「数组可能包含多个峰值，在这种情况下，返回任何一个所在位置即可」，
样例 1 的说明也写着「返回 4 的索引 1 或者 8 的索引 5 都可以」。
所以不能拿样例给的那个下标去死比——任何 O(log n) 的二分解法在
`[2,4,1,2,7,8,4]` 上都会走到右边那座山峰（下标 5），照样是对的。
要想让下标恰好等于 1，只能线性扫首个峰，那就违背了题目的进阶要求。

校验规则就是峰值的定义：严格大于左右邻，越界一侧视作 -∞。
"""


def check(inp: str, out) -> bool:
    nums = _parse(inp)
    if not nums:
        return False
    try:
        i = int(out)
    except (TypeError, ValueError):
        return False
    if not 0 <= i < len(nums):
        return False
    left_ok = i == 0 or nums[i] > nums[i - 1]
    right_ok = i == len(nums) - 1 or nums[i] > nums[i + 1]
    return left_ok and right_ok


def _parse(inp: str) -> list:
    """样例输入是牛客写法的一维数组：`[2,4,1,2,7,8,4]`。"""
    body = (inp or "").strip().strip("{}[]")
    out = []
    for tok in body.split(","):
        tok = tok.strip()
        if tok:
            out.append(int(tok))
    return out

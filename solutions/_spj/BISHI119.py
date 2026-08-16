"""BISHI119 校验器：答案区间不唯一，需要真正数一遍 "01" 子序列个数。

check(inp, out) 规则：
  - 选手输出 -1 时，暴力/前缀和验证「确实不存在任何区间恰好有 k 个」；
  - 否则解析 l, r，校验 1 <= l <= r <= n，并数出 s[l..r] 内的 01 子序列个数 == k。
"""


def _pairs(s, l, r):
    """s[l..r]（1-indexed 闭区间）内 "01" 子序列的个数。"""
    zeros = 0
    cnt = 0
    for i in range(l - 1, r):
        if s[i] == "1":
            cnt += zeros
        else:
            zeros += 1
    return cnt


def _exists(s, n, k):
    """是否存在某个区间恰好有 k 个 01 子序列（双指针，O(n)）。"""
    r = 0
    zeros = ones = pairs = 0
    for l in range(1, n + 1):
        if r < l - 1:
            r = l - 1
            zeros = ones = pairs = 0
        while r < n and pairs < k:
            c = s[r]
            r += 1
            if c == "1":
                pairs += zeros
                ones += 1
            else:
                zeros += 1
        if pairs == k:
            return True
        if r >= n and pairs < k:
            return False
        if r >= l:
            if s[l - 1] == "1":
                ones -= 1
            else:
                zeros -= 1
                pairs -= ones
    return False


def check(inp: str, out: str) -> bool:
    it = inp.split()
    n = int(it[0]); k = int(it[1])
    s = it[2]
    tok = out.split()
    if not tok:
        return False
    if tok[0] == "-1":
        return len(tok) == 1 and not _exists(s, n, k)
    if len(tok) != 2:
        return False
    try:
        l, r = int(tok[0]), int(tok[1])
    except ValueError:
        return False
    if not (1 <= l <= r <= n):
        return False
    return _pairs(s, l, r) == k

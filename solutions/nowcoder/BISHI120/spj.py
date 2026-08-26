"""BISHI120 校验器：多余的 '?' 可以填任意字母，答案不唯一。

check(inp, out) 规则（逐组用例）：
  - YES：输出串长度必须等于 |s|、只含小写字母、与 s 的非 '?' 位逐位相同，
         且 t 是它的子序列；
  - NO ：必须确实无解（用贪心重新判一遍）。
"""


def _feasible(s, t):
    j = 0
    lt = len(t)
    for c in s:
        if j >= lt:
            break
        if c == "?" or c == t[j]:
            j += 1
    return j == lt


def _is_subseq(t, u):
    j = 0
    lt = len(t)
    for c in u:
        if j < lt and c == t[j]:
            j += 1
    return j == lt


def check(inp: str, out: str) -> bool:
    it = inp.split()
    tok = out.split()
    T = int(it[0])
    p = 1
    q = 0
    for _ in range(T):
        s = it[p]; t = it[p + 1]
        p += 2
        if q >= len(tok):
            return False
        verdict = tok[q]; q += 1
        ok = _feasible(s, t)
        if verdict == "NO":
            if ok:
                return False
            continue
        if verdict != "YES":
            return False
        if not ok:
            return False
        if q >= len(tok):
            return False
        u = tok[q]; q += 1
        if len(u) != len(s):
            return False
        for a, b in zip(s, u):
            if not ("a" <= b <= "z"):
                return False
            if a != "?" and a != b:
                return False
        if not _is_subseq(t, u):
            return False
    return q == len(tok)

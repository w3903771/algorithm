"""BISHI52 奥赛组队 的特殊评测器。

答案不唯一：只要总实力达到最优，编程队/体育队的具体人选可以任意。
本校验器做四件事：
  1. 独立算出最优总实力 opt（按 a-b 降序 + 枚举分界点 + 前/后缀「前 k 大之和」）；
  2. 检查选手输出的第一行等于 opt；
  3. 检查第二/三行是 p 个、s 个互不相同且互不相交的合法编号（1..n）；
  4. 检查这两队的实际实力之和确实等于第一行报出的数（自洽性）。
"""
import heapq


def _optimum(n, p, s, a, b):
    order = sorted(range(n), key=lambda i: b[i] - a[i])   # a-b 降序

    f = [0] * (n + 1)          # 前 t 个里 a 最大的 p 个之和
    h, cur = [], 0
    for t in range(1, n + 1):
        v = a[order[t - 1]]
        if len(h) < p:
            heapq.heappush(h, v)
            cur += v
        elif p and v > h[0]:
            cur += v - heapq.heapreplace(h, v)
        f[t] = cur

    g = [0] * (n + 1)          # 后 n-t 个里 b 最大的 s 个之和
    h, cur = [], 0
    for t in range(n - 1, -1, -1):
        v = b[order[t]]
        if len(h) < s:
            heapq.heappush(h, v)
            cur += v
        elif s and v > h[0]:
            cur += v - heapq.heapreplace(h, v)
        g[t] = cur

    return max(f[t] + g[t] for t in range(p, n - s + 1))


def check(inp: str, out: str) -> bool:
    d = inp.split()
    n, p, s = int(d[0]), int(d[1]), int(d[2])
    a = [int(x) for x in d[3:3 + n]]
    b = [int(x) for x in d[3 + n:3 + 2 * n]]

    lines = [ln.strip() for ln in out.replace("\r\n", "\n").split("\n")]
    # p 或 s 为 0 时对应的行本来就是空行，所以不能无脑丢掉末尾空行，补齐到 3 行即可
    while len(lines) < 3:
        lines.append("")
    if any(ln for ln in lines[3:]):
        return False
    lines = lines[:3]

    try:
        claimed = int(lines[0])
        team_p = [int(x) for x in lines[1].split()]
        team_s = [int(x) for x in lines[2].split()]
    except ValueError:
        return False

    if len(team_p) != p or len(team_s) != s:
        return False
    ids = team_p + team_s
    if any(i < 1 or i > n for i in ids):
        return False
    if len(set(ids)) != len(ids):            # 队内不重复 + 两队不相交
        return False

    real = sum(a[i - 1] for i in team_p) + sum(b[i - 1] for i in team_s)
    return claimed == real == _optimum(n, p, s, a, b)

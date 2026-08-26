"""BISHI38 有向二分图构造 —— special judge。

选手只输出「核心边的编号集合 S」，并没有输出染色方案，所以校验器要做两件事：

  1. 数量达标：|S| >= floor(M/4) + 1，且编号互异、落在 [1, M] 内；

  2. **存在性**：确实存在一种黑白染色，使得核心边集合恰好等于 S。
     设 x_v = 1 表示 v 染黑。约束是：
       - 对 e=(u,v) ∈ S：x_u = 1 且 x_v = 0；
       - 对 e=(u,v) ∉ S：¬(x_u=1 ∧ x_v=0)，即蕴含式 x_u -> x_v。
     这些蕴含式是单调的，所以「把所有被强制为黑的点沿非 S 边做前向闭包」
     得到的 T 就是**最小**的合法黑点集合。若这个最小解都不合法
     （某条 S 边的终点落进了 T），那么任何染色都不合法。
     最后再用 T 显式重算一遍核心边集合并与 S 比对，双保险。
"""
from collections import deque


def _check_one(n, m, eu, ev, ids):
    need = m // 4 + 1
    k = len(ids)
    if k < need:
        return False
    if len(set(ids)) != k:
        return False
    if any(i < 1 or i > m for i in ids):
        return False

    core = set(ids)
    black = bytearray(n + 1)
    dq = deque()
    for i in core:
        u = eu[i - 1]
        if not black[u]:
            black[u] = 1
            dq.append(u)

    # 非核心边的蕴含关系 u -> v（u 黑则 v 必须也黑，否则这条边会变成核心边）
    adj = [[] for _ in range(n + 1)]
    for i in range(1, m + 1):
        if i not in core:
            adj[eu[i - 1]].append(ev[i - 1])

    while dq:
        u = dq.popleft()
        for v in adj[u]:
            if not black[v]:
                black[v] = 1
                dq.append(v)

    # 用这组最小染色重算核心边，必须与选手给出的集合完全一致
    got = set()
    for i in range(1, m + 1):
        if black[eu[i - 1]] and not black[ev[i - 1]]:
            got.add(i)
    return got == core


def check(inp: str, out: str) -> bool:
    it = iter(inp.split())
    ot = iter(out.split())
    try:
        T = int(next(it))
        for _ in range(T):
            n = int(next(it)); m = int(next(it))
            eu = [0] * m
            ev = [0] * m
            for i in range(m):
                eu[i] = int(next(it))
                ev[i] = int(next(it))
            k = int(next(ot))
            ids = [int(next(ot)) for _ in range(k)]
            if not _check_one(n, m, eu, ev, ids):
                return False
    except (StopIteration, ValueError):
        return False
    return True

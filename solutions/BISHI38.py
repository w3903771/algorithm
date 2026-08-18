"""BISHI38 有向二分图构造 —— 黑白染点，使「黑 -> 白」的核心边数 >= floor(M/4)+1。

这题考什么：
    先看阈值为什么一定能达到。随机把每个点独立地等概率染黑/白，
    每条边成为核心边的概率是 1/2 * 1/2 = 1/4，所以
        E[核心边数] = M / 4。
    核心边数是整数，而全黑染色给出 0 < M/4（M >= 1），说明它不是常数，
    于是**必然存在某种染色使核心边数严格大于 M/4**；
    而「整数 > M/4」等价于「>= floor(M/4)+1」，恰好就是题目要求。
    （这也解释了题面里那句「保证一定存在解」。）

    怎么把它构造出来：用**局部搜索（爬山）**直接最大化核心边数。
      - 记 outW(v) = v 指向白点的出边数，inB(v) = 黑点指向 v 的入边数。
        因为没有自环，翻转 v 的颜色只影响与 v 相邻的边：
          v 是黑 -> 翻成白：增量 = inB(v) - outW(v)；
          v 是白 -> 翻成黑：增量 = outW(v) - inB(v)。
      - 维护一个待检查队列，只要某点翻转能严格增加答案就翻，并把受影响的
        邻居重新入队。每次翻转答案至少 +1，而答案上界是 M，所以一定终止。
      - 收敛后再比较「整体取反」的染色（其核心边数 = 白->黑 的边数），
        取更优者继续爬山。这一步很关键：单点翻转对「所有边都是白->黑」
        这类局面是无能为力的，整体取反一步就翻盘。
    初始解取 outdeg(v) >= indeg(v) 就染黑，出度大的点当源、入度大的点当汇，
    起点质量高，通常一两轮就远超阈值。极端情况下再做若干次固定种子的
    随机重启（保证同一输入多次运行结果一致）。

数据规模与复杂度：
    T <= 10，N <= 1e5，M <= 2e5。
    建图 O(N+M)，一轮爬山的均摊代价是 O(∑翻转点的度数)，实测只有常数轮，
    整体近似 O(N + M)。用邻接表 + bytearray 存颜色，内存也够。

坑在哪：
    1. 阈值是「>= floor(M/4)+1」，**严格大于 M/4**，所以「随机一次取
       期望值」是不够的，必须做爬山/重启把它推过去；
    2. 图有重边（题面明说不保证无重边），所有统计都必须按「边」而不是
       「点对」来算，邻接表里要保留重复项；
    3. 要输出的是核心边的**编号**（1..M，按输入顺序），不是端点；
    4. 多组数据，且 ∑M 可能到 2e6，读入必须整块 buffer.read().split()；
    5. 答案不唯一：达到阈值的染色方案通常有很多种，对应的核心边编号集合也就
       不止一个。样例第二组的参考输出是「2 条边：1 4」，本解法给出的是
       「3 条边：1 3 4」，两者都满足 >= floor(4/4)+1 = 2。
       所以本地要用 special judge（特殊评测程序，按题目条件验证选手输出是否
       合法，而不是与标准答案逐字符比对）：本题配了 solutions/_spj/BISHI38.py。
       它不能只数个数——选手并没有输出染色方案，校验器必须反推出
       「是否存在一种染色，使核心边集合恰好等于输出的编号集合 S」：
       把 S 中每条边的起点强制染黑，再沿非 S 边做前向闭包得到最小黑点集，
       用这组染色重算一遍核心边并与 S 比对。
"""
import random
import sys
from collections import deque


def solve(n, m, eu, ev, out_adj, in_adj, color):
    """在给定初始 color 上做爬山，返回最终核心边数。"""
    # outW[v]: v 指向白点的出边数; inB[v]: 黑点指向 v 的入边数
    outW = [0] * (n + 1)
    inB = [0] * (n + 1)
    for i in range(m):                     # 一趟扫边把两张增量表填好
        u, v = eu[i], ev[i]
        if not color[v]:
            outW[u] += 1
        if color[u]:
            inB[v] += 1
    core = 0
    for v in range(1, n + 1):
        # 核心边「起点黑、终点白」，按起点归类即可不重不漏地数完
        if color[v]:
            core += outW[v]

    dq = deque(range(1, n + 1))
    inq = bytearray([1]) * (n + 1)         # 初始所有点都待检查
    while dq:
        v = dq.popleft()
        inq[v] = 0
        # 翻转 v 只影响与 v 相邻的边，增量可以 O(1) 算出来：
        # 黑翻白，v 的入边由「黑->白」变成核心边（+inB），出边不再是核心边（-outW）
        if color[v]:
            delta = inB[v] - outW[v]
        else:
            delta = outW[v] - inB[v]
        if delta <= 0:                     # 只走严格变优的一步，保证必然终止
            continue
        core += delta
        if color[v]:                       # 黑 -> 白
            color[v] = 0
            for w in out_adj[v]:           # v 不再是黑起点，出边邻居的 inB 减一
                inB[w] -= 1
                if not inq[w]:
                    inq[w] = 1
                    dq.append(w)
            for u in in_adj[v]:            # v 变成白终点，入边邻居的 outW 加一
                outW[u] += 1
                if not inq[u]:             # 受影响的点重新排队，等待再评估
                    inq[u] = 1
                    dq.append(u)
        else:                              # 白 -> 黑（与上面完全对称）
            color[v] = 1
            for w in out_adj[v]:
                inB[w] += 1
                if not inq[w]:
                    inq[w] = 1
                    dq.append(w)
            for u in in_adj[v]:
                outW[u] -= 1
                if not inq[u]:
                    inq[u] = 1
                    dq.append(u)
    return core


def count_core(m, eu, ev, color):
    """按给定染色数出核心边（起点黑、终点白）的条数。"""
    c = 0
    for i in range(m):                     # 重新数一遍，用于比较两种染色的优劣
        if color[eu[i]] and not color[ev[i]]:
            c += 1
    return c


def main() -> None:
    data = sys.stdin.buffer.read().split()
    p = 0
    T = int(data[p]); p += 1
    rng = random.Random(20240816)          # 固定种子：同一输入多次运行结果一致
    out = []
    for _ in range(T):
        n = int(data[p]); m = int(data[p + 1]); p += 2
        eu = [0] * m
        ev = [0] * m
        out_adj = [[] for _ in range(n + 1)]
        in_adj = [[] for _ in range(n + 1)]
        for i in range(m):
            u = int(data[p]); v = int(data[p + 1]); p += 2
            eu[i] = u; ev[i] = v           # 边表留着，翻转后要重新数核心边
            out_adj[u].append(v)           # 正反邻接表都要：翻转 v 时两侧都受影响
            in_adj[v].append(u)

        need = m // 4 + 1                  # 题目阈值：核心边数达到它即可收工
        # 初始解：出度不小于入度的点当「源」染黑，其余染白
        color = bytearray(n + 1)
        for v in range(1, n + 1):
            color[v] = 1 if len(out_adj[v]) >= len(in_adj[v]) else 0

        best = None
        best_core = -1
        # 至多 12 轮「爬山 + 随机重启」；一旦达标就 break，通常第一轮就够
        for attempt in range(12):
            core = solve(n, m, eu, ev, out_adj, in_adj, color)
            # 整体取反后核心边数 = 当前的「白 -> 黑」边数，更优就换过去再爬
            for _ in range(2):
                flipped = bytearray(color)
                for v in range(1, n + 1):
                    flipped[v] = 1 - flipped[v]
                c2 = count_core(m, eu, ev, flipped)
                if c2 > core:
                    color = flipped
                    core = solve(n, m, eu, ev, out_adj, in_adj, color)
                else:
                    break
            if core > best_core:
                best_core = core
                best = bytearray(color)
            if best_core >= need:
                break
            # 没过阈值就随机重启（种子固定，行为可复现）
            color = bytearray(n + 1)
            for v in range(1, n + 1):
                color[v] = rng.getrandbits(1)

        color = best                       # 取历轮中最好的一组染色
        # 输出的是边的编号（1-based，按输入顺序），不是端点
        ids = [str(i + 1) for i in range(m) if color[eu[i]] and not color[ev[i]]]
        out.append(str(len(ids)))
        out.append(" ".join(ids))
    sys.stdout.write("\n".join(out) + "\n")


main()

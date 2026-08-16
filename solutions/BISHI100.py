"""BISHI100 【模板】二分图判定 —— 无向图染色判二分图，n, m <= 3e5。

这题考什么：
    二分图 <=> 不存在奇环 <=> 可以用两种颜色染色使每条边两端异色。
    做法就是遍历每个未染色的点，从它开始 BFS/DFS 交替染 0/1，
    一旦发现某条边两端同色就判 NO。

数据规模与复杂度：
    n, m <= 3e5。O(n + m)。

Python 的坑（本题必看）：
  1. 题面写「保证连通」，但**样例 2 实际上是不连通的**（1-2-3 三角形 + 4-5）。
     所以绝不能只从 1 号点搜一次就收工，必须对每个未染色点都起一轮，
     否则会漏掉别的连通块里的奇环。这是本题最大的坑；
  2. **BFS + collections.deque，不用递归**：3e5 个点的链会把递归打爆，
     且 deque.popleft 是 O(1)（list.pop(0) 是 O(n)，会退化成平方）；
  3. 邻接表用 **CSR（三数组：起点偏移 + 目标数组）** 而不是 list of list：
     3e5 个点意味着 3e5 个小 list 对象，仅对象头就上百 MB，
     CSR 只有两个大数组，内存和缓存都好得多；也不要 defaultdict(list)；
  4. 存在重边，对染色判定毫无影响，不必去重。

CSR 构建方式：
    先统计每个点的度数 -> 前缀和得到每个点在大数组里的起始下标 ->
    再扫一遍边把邻居填进去。全程 O(n + m)，没有 append 扩容开销。
"""
import sys
from collections import deque


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n, m = int(data[0]), int(data[1])
    us = data[2::2][:m]
    vs = data[3::2][:m]
    us = [int(x) for x in us]
    vs = [int(x) for x in vs]

    # ---- CSR 邻接表 ----
    deg = [0] * (n + 2)
    for x in us:
        deg[x] += 1
    for x in vs:
        deg[x] += 1
    start = [0] * (n + 2)
    s = 0
    for i in range(1, n + 1):
        start[i] = s
        s += deg[i]
    start[n + 1] = s
    pos = start[:]
    adj = [0] * s
    for i in range(m):
        a = us[i]; b = vs[i]
        adj[pos[a]] = b; pos[a] += 1
        adj[pos[b]] = a; pos[b] += 1

    color = bytearray(n + 1)          # 0 = 未染色，1 / 2 = 两种颜色
    q = deque()
    for root in range(1, n + 1):
        if color[root]:
            continue
        color[root] = 1
        q.append(root)
        while q:                      # 图可能不连通，逐个连通块处理
            u = q.popleft()
            cu = color[u]
            nc = 3 - cu               # 1 <-> 2
            for i in range(start[u], start[u + 1]):
                v = adj[i]
                cv = color[v]
                if cv == 0:
                    color[v] = nc
                    q.append(v)
                elif cv == cu:        # 同色边 -> 存在奇环
                    sys.stdout.write("NO\n")
                    return
    sys.stdout.write("YES\n")


main()

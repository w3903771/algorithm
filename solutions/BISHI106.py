"""BISHI106 【模板】单源最短路 III ‖ 非负权图：Dijkstra —— 有向非负权图的单源最短路。

这题考什么：
    Dijkstra + 二叉堆。边权非负（可以为 0）时，每次取出「当前 dist 最小
    且未定型」的点，它的 dist 就已经是最终答案，然后拿它去松弛出边。

    Python 里的标准写法是 **heapq 的「懒删除」版本**：
      - 不做 decrease-key（heapq 不支持），松弛成功就直接 heappush 一个新的 (d, v)；
      - 弹出 (d, u) 时若 d > dist[u]，说明这是过期的旧记录，**直接 continue 跳过**。
    堆里最多有 O(m) 个元素，复杂度 O(m log m)。

数据规模与复杂度：
    n, m <= 2e5，w <= 1e9。O(m log m) ≈ 2e5 * 18。
    朴素 O(n^2) 的 Dijkstra 是 4e10，只有在 n 很小（比如几百）时才该用。

Python 的坑（本题必看）：
  1. 堆里存**元组 (d, v)**，比较先按 d 再按 v，天然正确；
  2. 懒删除的 `if d > dist[u]: continue` 一定要写，否则同一个点会被重复展开，
     退化成指数级的松弛次数；
  3. 邻接表用 **CSR（Compressed Sparse Row，压缩稀疏行：把整张图压进三个扁平
     数组 start / to / wt，start[u] 到 start[u+1] 之间就是 u 的全部出边）**，
     不要 defaultdict(list) 也不要 list of list of tuple——
     2e5 个小 list 加 2e5 个元组对象的构造和内存开销很可观；
  4. dist 初值用 -1 表示不可达 + 一个大常数 INF 表示「还没算出来」，
     这里统一用 INF 计算、输出时把仍为 INF 的换成 -1。

坑在哪：
  1. 图**有向**、可能不连通、可能有重边、边权可以是 0
     （样例 1 里 1->4 权 0，答案 dist[4] = 1 走的是 2->1->4）；
  2. 起点自己输出 0；
  3. 边权和最大 2e5 * 1e9 = 2e14，C++ 要 long long，Python 无忧。
"""
import sys
from heapq import heappush, heappop


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); m = int(data[1]); s = int(data[2])

    # ---- CSR 邻接表（有向带权），分三趟建好 ----
    # 第一趟：只统计每个点的出度，暂不关心边的内容。
    deg = [0] * (n + 2)
    for i in range(3, 3 + 3 * m, 3):     # 每条边占 3 个 token，步长 3 恰好只取到 u
        deg[int(data[i])] += 1
    # 第二趟：出度做前缀和，start[u] 即点 u 的边在 to/wt 中的起始下标。
    start = [0] * (n + 2)
    acc = 0
    for i in range(1, n + 1):
        start[i] = acc
        acc += deg[i]
    start[n + 1] = acc                   # 末尾哨兵：u 的边区间是 [start[u], start[u+1])
    pos = start[:]                       # 填充游标，pos[u] 指向 u 的下一条边该落在哪
    to = [0] * acc
    wt = [0] * acc
    p = 3
    # 第三趟：真正把边写进扁平数组，同源的边自然连成一段。
    for _ in range(m):
        u = int(data[p]); v = int(data[p + 1]); w = int(data[p + 2]); p += 3
        k = pos[u]
        to[k] = v; wt[k] = w
        pos[u] = k + 1                   # 游标后移，下一条以 u 为起点的边接着放

    # ---- Dijkstra 主循环：堆中元素是 (已知距离, 点号) ----
    INF = float('inf')
    dist = [INF] * (n + 1)               # INF 同时兼作「还没被松弛到」的标记
    dist[s] = 0
    heap = [(0, s)]
    while heap:
        d, u = heappop(heap)
        if d > dist[u]:              # 懒删除：过期记录直接丢掉
            continue
        # 走到这里 dist[u] 已经定型，用它松弛 u 的每一条出边
        for i in range(start[u], start[u + 1]):
            v = to[i]
            nd = d + wt[i]
            if nd < dist[v]:
                dist[v] = nd
                heappush(heap, (nd, v))  # 不改堆里的旧记录，直接压一条更优的进去

    # 仍为 INF 的点说明从 s 走不到，按题面要求输出 -1
    out = [(str(x) if x != INF else "-1") for x in dist[1:]]
    sys.stdout.write(" ".join(out) + "\n")


main()

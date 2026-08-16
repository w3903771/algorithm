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
  3. 邻接表用 **CSR（三个扁平数组：start / to / wt）**，不要 defaultdict(list)
     也不要 list of list of tuple——2e5 个点 + 2e5 个元组对象的开销很可观；
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

    # ---- CSR 邻接表（有向带权）----
    deg = [0] * (n + 2)
    for i in range(3, 3 + 3 * m, 3):
        deg[int(data[i])] += 1
    start = [0] * (n + 2)
    acc = 0
    for i in range(1, n + 1):
        start[i] = acc
        acc += deg[i]
    start[n + 1] = acc
    pos = start[:]
    to = [0] * acc
    wt = [0] * acc
    p = 3
    for _ in range(m):
        u = int(data[p]); v = int(data[p + 1]); w = int(data[p + 2]); p += 3
        k = pos[u]
        to[k] = v; wt[k] = w
        pos[u] = k + 1

    INF = float('inf')
    dist = [INF] * (n + 1)
    dist[s] = 0
    heap = [(0, s)]
    while heap:
        d, u = heappop(heap)
        if d > dist[u]:              # 懒删除：过期记录直接丢掉
            continue
        for i in range(start[u], start[u + 1]):
            v = to[i]
            nd = d + wt[i]
            if nd < dist[v]:
                dist[v] = nd
                heappush(heap, (nd, v))

    out = [(str(x) if x != INF else "-1") for x in dist[1:]]
    sys.stdout.write(" ".join(out) + "\n")


main()

"""BISHI109 邮递员送信 —— 从 1 号点分别往返 2..n 各一次，求总最短时间。

这题考什么：
    「所有点到某个源点的最短路」= **在反向图上从源点跑一次单源最短路**。

    总时间 = Σ_{v=2..n} ( dist(1 -> v) + dist(v -> 1) )。
      - 前半部分：在**原图**上从 1 跑一次 Dijkstra，求出 dist(1 -> v)；
      - 后半部分：dist(v -> 1) 若逐点跑就是 n 次 Dijkstra（n=1000 时 1e8 级别），
        正确做法是把所有边**反向**建图，在反图上从 1 跑一次 Dijkstra，
        得到的 rdist[v] 恰好就是原图里 v -> 1 的最短路。
    于是只需要**两次** Dijkstra。

数据规模与复杂度：
    n <= 1e3，m <= 1e5，w <= 1e4。两次堆优化 Dijkstra 各 O(m log m)。
    （n 只有 1000，朴素 O(n^2) 的 Dijkstra 也是 1e6 能过，
      但 m 到 1e5 时堆优化更稳，而且是通用写法。）

Python 的坑：
  1. Dijkstra 用 heapq，标准「懒删除」写法：弹出 (d, u) 时若 d > dist[u]
     就 continue，heapq 没有 decrease-key，这是唯一正确的姿势；
  2. 两张 CSR 邻接表（正图、反图）共用同一套构建代码，写成函数复用；
     不要用 defaultdict(list)；
  3. 输入 3e5 个整数一次 read().split()。

坑在哪：
  1. 题面保证「任意两点互相可达」，所以不会出现 INF；
     但保险起见仍按 INF 处理（真出现就说明数据违背题面）；
  2. **道路是单向的**，反图必须真的把 u、v 换个位置重新建表，
     不能直接复用原图；
  3. 可能有重边（样例里 3->5 出现两次，权都是 6），Dijkstra 天然处理；
  4. 答案可达 1e3 * 2 * (1e3 * 1e4) = 2e10 级别，C++ 要 long long；Python 无忧。
"""
import sys
from heapq import heappush, heappop


def build_csr(n, us, vs, ws):
    """把边表压成 CSR：返回 (start, to, wt)。"""
    m = len(us)
    deg = [0] * (n + 2)
    for u in us:
        deg[u] += 1
    start = [0] * (n + 2)
    acc = 0
    for i in range(1, n + 1):
        start[i] = acc
        acc += deg[i]
    start[n + 1] = acc
    pos = start[:]
    to = [0] * acc
    wt = [0] * acc
    for i in range(m):
        u = us[i]
        k = pos[u]
        to[k] = vs[i]; wt[k] = ws[i]
        pos[u] = k + 1
    return start, to, wt


def dijkstra(n, start, to, wt, src):
    INF = float('inf')
    dist = [INF] * (n + 1)
    dist[src] = 0
    heap = [(0, src)]
    while heap:
        d, u = heappop(heap)
        if d > dist[u]:              # 懒删除
            continue
        for i in range(start[u], start[u + 1]):
            v = to[i]
            nd = d + wt[i]
            if nd < dist[v]:
                dist[v] = nd
                heappush(heap, (nd, v))
    return dist


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n, m = int(data[0]), int(data[1])
    us = [0] * m; vs = [0] * m; ws = [0] * m
    p = 2
    for i in range(m):
        us[i] = int(data[p]); vs[i] = int(data[p + 1]); ws[i] = int(data[p + 2])
        p += 3

    d1 = dijkstra(n, *build_csr(n, us, vs, ws), src=1)   # 去程：1 -> v
    d2 = dijkstra(n, *build_csr(n, vs, us, ws), src=1)   # 回程：反图上 1 -> v 即 v -> 1

    total = 0
    for v in range(2, n + 1):
        total += d1[v] + d2[v]
    sys.stdout.write("%d\n" % total)


main()

"""BISHI105 【模板】单源最短路 I ‖ 无权图：BFS —— 有向无权图的单源最短路。

这题考什么：
    **无权图（每条边权都是 1）的最短路就是 BFS**，不要上 Dijkstra。
    BFS 按层扩展，第一次访问到某点时的层号就是最短距离，复杂度 O(n + m)；
    而 Dijkstra 要多背一个堆，是 O(m log n)，纯属浪费。

数据规模与复杂度：
    n, m <= 2e5，O(n + m)。

Python 的坑（本题必看）：
  1. **队列必须是 collections.deque**。用 list.pop(0) 每次弹头都要搬移整个
     列表，2e5 个点会退化成 O(n^2) = 4e10，必 TLE；
  2. 邻接表用 **CSR（度数前缀和 + 一个扁平数组）**，不要 defaultdict(list)：
     2e5 个点各建一个 list 对象光对象头就几十 MB，而且哈希/扩容都是额外开销；
  3. dist 初始化为 -1，既当「未访问」标记又是最终「不可达」的输出值；
  4. 输出是**一行** n 个整数，用 " ".join(map(str, ...)) 一次写出。

坑在哪：
  1. 图**有向**，建表时只加 u -> v 一条方向，别顺手加反向；
  2. 图可能不连通、可能有重边（样例 1 里 4->3 出现了两次），
     BFS 对重边天然免疫（第二次看到时 dist 已经填过了）；
  3. dist[s] = 0 要先设好再入队。
"""
import sys
from collections import deque


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); m = int(data[1]); s = int(data[2])

    # ---- CSR 邻接表（有向）----
    deg = [0] * (n + 2)
    for i in range(3, 3 + 2 * m, 2):
        deg[int(data[i])] += 1
    start = [0] * (n + 2)
    acc = 0
    for i in range(1, n + 1):
        start[i] = acc
        acc += deg[i]
    start[n + 1] = acc
    pos = start[:]
    adj = [0] * acc
    p = 3
    for _ in range(m):
        u = int(data[p]); v = int(data[p + 1]); p += 2
        adj[pos[u]] = v
        pos[u] += 1

    dist = [-1] * (n + 1)
    dist[s] = 0
    q = deque([s])                      # 必须 deque
    while q:
        u = q.popleft()
        d = dist[u] + 1
        for i in range(start[u], start[u + 1]):
            v = adj[i]
            if dist[v] < 0:
                dist[v] = d
                q.append(v)
    sys.stdout.write(" ".join(map(str, dist[1:])) + "\n")


main()

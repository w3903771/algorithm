"""BISHI105 【模板】单源最短路 I ‖ 无权图：BFS —— 有向无权图的单源最短路。

这题考什么：
    **无权图（每条边权都是 1）的最短路就是 BFS**，不要上 Dijkstra。
    BFS 按层扩展，第一次访问到某点时的层号就是最短距离，复杂度 O(n + m)；
    BFS 框架见 docs/part5-搜索/61-BFS广度优先搜索.md，
    带权图的最短路见 docs/part8-图与树/91-最短路.md；
    而 Dijkstra 要多背一个堆，是 O(m log n)，纯属浪费。

数据规模与复杂度：
    n, m <= 2e5，O(n + m)。

Python 的坑（本题必看）：
  1. **队列必须是 collections.deque**。用 list.pop(0) 每次弹头都要搬移整个
     列表，2e5 个点会退化成 O(n^2) = 4e10，必 TLE；
  2. 邻接表用 **CSR（压缩稀疏行：所有出边挤在一个扁平数组里，
     再用出度前缀和标出每个点占哪一段）**，不要 defaultdict(list)：
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
    # 第一步：数出度。起点 u 落在 token 流的第 3, 5, 7, ... 位
    deg = [0] * (n + 2)
    for i in range(3, 3 + 2 * m, 2):
        deg[int(data[i])] += 1
    # 第二步：出度前缀和，start[u] 是 u 的出边在 adj 中的起始下标
    start = [0] * (n + 2)
    acc = 0
    for i in range(1, n + 1):
        start[i] = acc
        acc += deg[i]
    start[n + 1] = acc                  # 末位哨兵，出边区间恒为 [start[u], start[u+1])
    # 第三步：pos 记录各点写到哪，再扫一遍边把终点填进扁平数组
    pos = start[:]
    adj = [0] * acc
    p = 3
    for _ in range(m):
        u = int(data[p]); v = int(data[p + 1]); p += 2
        adj[pos[u]] = v                 # 有向图只存 u -> v 一个方向
        pos[u] += 1

    # ---- BFS：队列里的距离天然按层不减，出队时 dist 已是最终值 ----
    dist = [-1] * (n + 1)               # -1 既是「未访问」标记，也是不可达时的输出
    dist[s] = 0                         # 起点先设距离再入队，否则会被自己重复扩展
    q = deque([s])                      # 必须 deque
    while q:
        u = q.popleft()
        d = dist[u] + 1                 # u 的所有邻居都落在下一层
        for i in range(start[u], start[u + 1]):
            v = adj[i]
            if dist[v] < 0:             # 只在首次访问时赋值，重边自然被跳过
                dist[v] = d
                q.append(v)
    sys.stdout.write(" ".join(map(str, dist[1:])) + "\n")   # 一行 n 个整数一次写出


main()

"""BISHI108 最优乘车 —— 单向巴士线路，求 1 号站到 N 号站的最少换乘次数。

这题考什么：
    「最少换乘 = 最少乘车段数 - 1」的建图技巧。

    最朴素的建法是：同一条线路上任意「前面的站 -> 后面的站」连一条权 1 的边，
    然后 BFS。但一条线路有 s 个站就要连 s^2/2 条边，
    100 条 * 500 站 = 1.25e7 条边，Python 建图就先跪了。

    正确做法是**拆点建虚拟链**：对每条线路的每个位置 i 建一个「车上」节点 R_i，
      - R_i -> R_{i+1}：权 0（坐着不动，继续往前开）
      - 站台 t_i -> R_i：权 1（上车，多坐一趟车）
      - R_i -> 站台 t_i：权 0（下车，免费）
    这样边数只有 O(Σs) ≈ 1e5，而且**天然保留了线路的单向性**
    （在位置 i 上车只能到 i 之后的站，不会倒着坐）。

    边权只有 0 和 1，所以用 **0-1 BFS（双端队列）**：
    权 0 的边 appendleft、权 1 的边 append，出队顺序仍是距离单调不减，
    复杂度 O(V + E)，不需要 Dijkstra 的那个 log。

数据规模与复杂度：
    M <= 100 条线路，N <= 500 个站，每条线路 s <= N。
    点数 = N + Σs <= 500 + 5e4，边数 ≈ 3 * Σs。O(V + E)。

Python 的坑：
  1. 0-1 BFS 的队列**必须是 collections.deque**（要用 appendleft），
     list 根本没有 O(1) 的头插；
  2. 出队时要检查 `if d > dist[u]: continue`（同一个点可能被以更差的距离
     多次入队），这和 Dijkstra 的懒删除是同一个道理；
  3. 邻接表用定长 list of list，不要 defaultdict。

坑在哪：
  1. 输入第一行是 **M（线路数）在前、N（站数）在后**，顺序容易读反；
  2. 答案是「乘车段数 - 1」，无需换乘时输出 0；
  3. 到不了要输出 "NO"（大写）；
  4. 起点就是终点（N = 1）在本题不会出现（题面保证 N >= 2）。

样例复核：
    1 -> 上第 3 条线（2 1 3 5）在位置 2 -> 坐到 3（1 段）
      -> 上第 2 条线（4 7 3 6）在位置 3 -> 坐到 6（2 段）
      -> 上第 1 条线（6 7）在位置 1 -> 坐到 7（3 段）。换乘 3 - 1 = 2 ✓
"""
import sys
from collections import deque


def main() -> None:
    data = sys.stdin.buffer.read().split()
    M = int(data[0]); N = int(data[1])

    # ---- 逐条读线路：每条线路先给站数 s，再给 s 个站号 ----
    lines = []
    p = 2
    total_stops = 0                           # Σs，决定「车上」节点一共要开多少个
    for _ in range(M):
        s = int(data[p]); p += 1
        stops = [int(v) for v in data[p:p + s]]; p += s
        lines.append(stops)
        total_stops += s

    # ---- 建图 ----
    # 节点编号：1..N 是站台，N+1.. 是各线路各位置的「车上」节点
    V = N + total_stops + 1                   # 0 号下标空着不用，站台编号才能与题面对齐
    adj = [[] for _ in range(V)]
    nid = N + 1                               # 下一个可分配的「车上」节点编号
    for stops in lines:
        base = nid                            # 本条线路的第 i 站对应节点 base + i
        s = len(stops)
        for i, st in enumerate(stops):
            r = base + i
            adj[st].append((r, 1))            # 上车：算一趟车
            adj[r].append((st, 0))            # 下车：免费
            if i + 1 < s:
                adj[r].append((r + 1, 0))     # 继续往前开：免费，且只能顺向
        nid += s                              # 让出本条线路占用的 s 个编号

    # ---- 0-1 BFS：边权只有 0/1，用双端队列代替堆 ----
    INF = float('inf')
    dist = [INF] * V
    dist[1] = 0                               # 起点固定是 1 号站台
    dq = deque([(0, 1)])                      # 0-1 BFS 需要双端队列
    while dq:
        d, u = dq.popleft()
        if d > dist[u]:                       # 懒删除，过期记录跳过
            continue
        for v, w in adj[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                # 队列里始终只存在两种距离值 d 和 d+1，且 d 全在前面，
                # 所以按下面这样分头插入就能保持出队顺序单调不减
                if w:
                    dq.append((nd, v))        # 权 1 放队尾
                else:
                    dq.appendleft((nd, v))    # 权 0 放队首
    # dist[N] 是「乘车段数」（每次上车 +1），换乘次数要再减 1
    d = dist[N]
    sys.stdout.write("NO\n" if d == INF else "%d\n" % (d - 1))


main()

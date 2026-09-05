---
id: graph/shortest-path
title: 最短路
volume: 2
lang: py
---

# 第 91 章　最短路

<!-- CHAPTER-EXAMPLES -->
> **前置**：[图的表示与遍历](basic.md)、[优先队列与堆](../ds/heap.md)、[BFS广度优先搜索](../search/bfs.md)

最短路是图论里考得最多的一块，也是**最容易用错算法**的一块。
Python 选手尤其要记住一条：**能用 BFS 就别用 Dijkstra，能用 Dijkstra 就别用 SPFA**。
每往上升一级，常数就翻一倍。

---

## 1　松弛：所有最短路算法的共同内核

> 设置起点为 $s$，以及数组 $dist[x]$ 表示从 $s$ 到 $x$ 的最短路径的长度。
>
> 在已知当前的 $dist$ 的情况下，再往图中加入一条边 $e: u \to v$，边权为 $w$。
> 有可能会有部分最短路将经过 $e$。这就需要看 $e$ 能否使某些 $dist$ 变小，
> 也就是所谓的「**松弛**」。
>
> 如果 $dist[u] + w < dist[v]$，那么先从 $s$ 走到 $u$，再经过边 $e$，
> 会得到一条比以前更短的路径。

```python
# [片段] 松弛操作：所有最短路算法的唯一原子操作
if dist[u] + w < dist[v]:                    # 「先到 u 再走这条边」比现有记录更短
    dist[v] = dist[u] + w                    # 就把 v 的记录改小；否则什么都不做
```

**所有最短路算法的区别只有一个：以什么顺序、松弛多少次。**

| 算法 | 松弛顺序 |
| --- | --- |
| BFS | 按层，每条边松弛一次 |
| 0-1 BFS | 双端队列，权 0 优先 |
| Dijkstra | 按 $dist$ 从小到大，每个点定型后松弛其出边一次 |
| Bellman-Ford | 无脑把所有边松弛 $n-1$ 轮 |
| SPFA | 只松弛「$dist$ 刚变小」的点的出边 |
| Floyd | 按中转点 $k$ 从小到大，松弛所有点对 |

---

## 2　选型总表（本章最重要的一张表）

| 图的特征 | 算法 | 复杂度 | Python 现实规模 |
| --- | --- | --- | --- |
| **无权（边权全 1）** | **BFS** | $O(n+m)$ | $m \le 5\times10^5$ |
| **边权只有 0 和 1** | **0-1 BFS**（`deque`） | $O(n+m)$ | $m \le 5\times10^5$ |
| 边权是小整数 $0..k$ | 桶队列 / 分层图 | $O(k n + m)$ | 视 $k$ |
| **非负权，单源** | **Dijkstra + `heapq`** | $O(m\log m)$ | $m \le 2\times10^5$ |
| 非负权，**稠密**（$m \approx n^2$）且 $n$ 小 | 朴素 Dijkstra | $O(n^2)$ | $n \le 2000$ |
| 有负权，单源 | Bellman-Ford / SPFA | $O(nm)$ | $nm \le 10^6$ |
| **判负环** | Bellman-Ford / SPFA + 计数 | $O(nm)$ | $nm \le 10^6$ |
| **全源最短路**，$n$ 小 | **Floyd** | $O(n^3)$ | **$n \le 100$**（切片优化到 200） |
| 全源，$n$ 大但稀疏 | 跑 $n$ 次 Dijkstra | $O(nm\log m)$ | $n \le 1000$ 且 $m$ 小 |
| **所有点到某一个点** | **反图 + 一次单源** | 同单源 | — |

> **最高频的两个错误**：
> 1. **无权图上跑 Dijkstra**——白白多一个 $\log$ 和一个堆。BISHI105 考的就是这个；
> 2. **非负权图上跑 SPFA**——Python 下 SPFA 的常数比 `heapq` 还大，而且能被卡到 $O(nm)$。
>    **有 Dijkstra 可用时，永远不要用 SPFA。**

---

## 3　无权图：BFS 就是最短路

边权全为 1 时，BFS 按层扩展，**第一次访问到某点时的层号就是最短距离**。

本章的模板一律用 CSR（Compressed Sparse Row，压缩稀疏行）存图：
`start` 记每个点的邻居从大数组的哪一格开始，`adj` / `to` / `wt` 把所有邻居首尾相接，
于是 $u$ 的出边就是下标区间 $[\texttt{start[u]},\ \texttt{start[u+1]})$。
建表方法见 [图的表示与遍历 §2](basic.md)。

```python
from collections import deque


def bfs_sp(s, start, adj, n):
    """无权图单源最短路。O(n + m)。dist = -1 表示不可达。"""
    dist = [-1] * (n + 1)                    # -1 兼任「未访问」标记与「不可达」输出值
    dist[s] = 0
    q = deque([s])
    while q:
        u = q.popleft()                      # 队列按距离单调不减，队头一定已定型
        d = dist[u] + 1                      # 从 u 再走一条边，距离固定是 d
        for i in range(start[u], start[u + 1]):
            v = adj[i]
            if dist[v] < 0:                  # 只在「首次访问」时赋值
                dist[v] = d                  # 首次即最短，后面不会再有更小的值
                q.append(v)
    return dist
```

> **正确性**：BFS 的队列里距离值最多只有两种（$d$ 和 $d+1$），且单调不减。
> 所以第一次出队时的 `dist` 就是最终答案，不需要任何「定型」判断。

| | BFS | Dijkstra |
| --- | --- | --- |
| 复杂度 | $O(n+m)$ | $O(m\log m)$ |
| 每个点入队次数 | **恰好 1 次** | 最多 $\deg(u)$ 次（懒删除） |
| Python 常数 | `deque` 的 `append`/`popleft` 都是 C 层 $O(1)$ | 每次 `heappush` 要建元组 + 上浮 |
| $m = 2\times10^5$ 实测 | ~0.3 秒 | ~1.5 秒 |

**差 5 倍**。这就是为什么 BISHI105 单独出成一道题。

---

## 4　0-1 BFS：边权只有 0 和 1

> **权 0 的边 → `appendleft`（插队首）；权 1 的边 → `append`（排队尾）。**

```python
from collections import deque


def bfs01(s, adj, n):
    """0-1 BFS：边权只有 0/1 的最短路。O(n + m)，比 Dijkstra 快数倍。

    adj[u] = [(v, w), ...]，w in {0, 1}。
    正确性：队列中的距离值始终只有 d 和 d+1 两种且单调不减，
    所以 0 权边插队首、1 权边接队尾之后单调性依然成立。
    """
    INF = float("inf")
    dist = [INF] * n
    dist[s] = 0
    dq = deque([(0, s)])                     # 元素是 (当时的距离, 点号)
    while dq:
        d, u = dq.popleft()                  # 队头永远是全队最小距离
        if d > dist[u]:                      # 懒删除：过期副本直接丢
            continue                         # u 后来被更小的距离更新过，这份已作废
        for v, w in adj[u]:
            nd = d + w
            if nd < dist[v]:                 # 判据是「变小了」，不是「没访问过」
                dist[v] = nd
                if w:
                    dq.append((nd, v))       # 权 1 排队尾：它属于下一层 d+1
                else:
                    dq.appendleft((nd, v))   # 权 0 插队首：它仍属于当前层 d
    return dist
```

> ⚠️ **0-1 BFS 与普通 BFS 的关键区别**：**一个点可能被多次入队**
> （第二次以更小的距离进来），所以判定条件是 `nd < dist[v]`
> 而不是「没访问过」。出队时的 `if d > dist[u]: continue` 是必要的剪枝。

**0-1 BFS 的用武之地远比想象中大**，因为很多题能被建模成 0/1 权：

| 题面里的话 | 0/1 权建模 |
| --- | --- |
| 「最少换乘几次」 | 上车权 1，坐车 / 下车权 0（**BISHI108**） |
| 「最少打破几堵墙」 | 空地权 0，墙权 1 |
| 「最少转弯几次」 | 同方向权 0，转弯权 1（按方向拆点） |
| 「最少翻转几条边」 | 顺边权 0，逆边权 1 |

---

## 5　Dijkstra

「流水模型」是最直观的解释：

> 在起点插上一根水管，如果水流速度固定，那么最短路上的水流将会最先到达终点。
> 按照时间顺序模拟水流。每个状态记录水流到达的节点和到达的时间。
> 从初始状态开始（位置在起点并且时间为 0），之后每次抽出**时间最短**的状态，
> 尝试向四周流水。如果流到旁边的节点的时间小于记录的 `dist`，就说明当前是更快的水流。
> 使用堆来维护时间顺序即可，时间复杂度为 $O(m \log n)$。**这就是 Dijkstra 算法。**

**正确性的前提是边权非负**：每次取出的最小 `dist` 已经不可能再被任何后续路径变小，
因为后续路径只会更长（加上的边权 $\ge 0$）。**有负权则该前提崩塌，Dijkstra 直接错。**

### 朴素 $O(n^2)$ 版

参考实现是邻接矩阵 + 每轮线性扫描找最小值：

```cpp
// 找到离 1 号顶点最近的顶点
min = inf;
for (int j = 1; j <= n; ++j)
    if (book[j] == 0 && dis[j] < min) { min = dis[j]; u = j; }
book[u] = 1;
for (int v = 1; v <= n; ++v)
    if (dis[v] > dis[u] + edge[u][v]) dis[v] = dis[u] + edge[u][v];
```

Python 版可以把「找最小值」和「松弛一整行」**都下沉到 C 层**：

```python
def dijkstra_dense(g, n, s):
    """朴素 O(n^2) Dijkstra，邻接矩阵版。适用于稠密图且 n <= 2000。

    g 是 (n+1)x(n+1) 的邻接矩阵，不通为 INF（用大整数，不要用 float('inf')）。
    Python 技巧：用 min(...) 配合生成器找最小值，让比较落在 C 层。
    """
    INF = 1 << 60
    dist = [INF] * (n + 1)
    dist[s] = 0
    done = bytearray(n + 1)                  # done[u] = 1 表示 u 的最短路已定型
    for _ in range(n):                       # 每轮定型一个点，n 轮定完全图
        u = -1
        best = INF
        for j in range(1, n + 1):            # 找当前未定型的最小 dist
            if not done[j] and dist[j] < best:
                best = dist[j]
                u = j
        if u < 0:
            break                            # 剩下的都不可达
        done[u] = 1                          # 非负权保证：这个最小值不会再被改小
        gu = g[u]                            # ★ 绑成局部名，省属性/下标查找
        du = best
        for v in range(1, n + 1):            # 用刚定型的 u 松弛一整行
            nd = du + gu[v]                  # 不通时 gu[v] = INF，nd 大得没有威胁
            if nd < dist[v]:
                dist[v] = nd
    return dist
```

> **朴素版什么时候反而更好？** 当图**稠密**（$m \approx n^2$）时，
> 堆优化是 $O(n^2 \log n)$，反而不如朴素的 $O(n^2)$。
> 但在 Python 里这个分界点要往下挪：纯 Python 的双重循环 $n = 2000$ 就是 $4\times10^6$ 次迭代，
> 已经接近 1 秒。**$n > 2000$ 时无论稠密稀疏都请用堆优化版。**

### 堆优化 + 懒删除（Python 的标准写法）

```python
from heapq import heappush, heappop


def dijkstra(n, start, to, wt, s):
    """堆优化 Dijkstra（CSR 版），非负权。O(m log m)。

    教科书版 Dijkstra 需要 decrease-key（把堆里某个点的键改小），
    heapq 没有这个 API，于是改用「懒删除」：
      - 松弛成功就直接 push 一个新的 (d, v)，不去改堆里的旧记录；
      - 弹出 (d, u) 时若 d > dist[u]，说明是过期记录，直接跳过。
    堆里最多 O(m) 个元素，复杂度不变。
    """
    INF = float("inf")
    dist = [INF] * (n + 1)                   # 只做比较、不做 INF + w 的运算，所以能用 inf
    dist[s] = 0
    heap = [(0, s)]                          # 元素是 (距离, 点号)：元组比较先比距离
    while heap:
        d, u = heappop(heap)                 # 全堆最小距离 -> 非负权下 u 就此定型
        if d > dist[u]:                      # ★ 懒删除，这一行不能省
            continue                         # 同一个 u 的更小记录已经处理过了
        for i in range(start[u], start[u + 1]):
            v = to[i]
            nd = d + wt[i]                   # 经过 u 到 v 的距离
            if nd < dist[v]:                 # 松弛成功
                dist[v] = nd                 # dist 才是唯一真相，堆只是候选池
                heappush(heap, (nd, v))      # 旧记录留在堆里，出堆时被上面那行筛掉
    return dist
```

**关于懒删除的三条必须理解的事**：

| 问题 | 答案 |
| --- | --- |
| 为什么不做 decrease-key？ | `heapq` 根本没这个 API；手写「索引堆」在 Python 下比多 push 几次还慢 |
| 堆会不会爆？ | 最多 $m$ 个元素（每次成功松弛 push 一次），$m = 2\times10^5$ 完全没问题 |
| 不写 `if d > dist[u]: continue` 会怎样？ | 同一个点被重复展开，松弛次数指数级膨胀，**大数据必 TLE** |

> **为什么堆里存元组 `(d, v)` 而不是自定义类？**
> 元组比较是 C 层的字典序比较，先比 `d` 再比 `v`，天然正确且飞快。
> 自定义类要写 `__lt__`，每次比较都是一次 Python 函数调用，慢 5 倍以上。
> 见 [优先队列与堆](../ds/heap.md)。

### Dijkstra 的常见变形

```python
# [片段] 变形一：记录路径（前驱数组）
if nd < dist[v]:
    dist[v] = nd
    pre[v] = u                               # 记下是谁松弛的它
    heappush(heap, (nd, v))
# 还原：从终点沿 pre 一路回溯到起点，最后 reverse
# pre 只在松弛成功时被覆盖，所以它始终指向「当前最优路径」上的前一个点

# [片段] 变形二：最短路计数（边权 > 0 时正确）
if nd < dist[v]:
    dist[v] = nd
    cnt[v] = cnt[u]                          # 找到更短的路 -> 旧方案全部作废，重新计
    heappush(heap, (nd, v))
elif nd == dist[v]:
    cnt[v] += cnt[u]                         # 又找到一条同样长的路

# [片段] 变形三：多源最短路——把所有源点一起塞进初始堆
heap = [(0, s) for s in sources]             # 每个源点的初始距离都是 0
for s in sources:
    dist[s] = 0
heapify(heap)                                # O(k) 一次建堆，比逐个 heappush 快

# [片段] 变形四：次短路——每个点维护 dist1 / dist2 两个值
```

> ⚠️ **最短路计数在有 0 权边时会算错**：0 权边可能让 `nd == dist[v]` 在 $v$
> 已经定型之后才发生。稳妥做法是**先跑一次 Dijkstra 定出 `dist`，
> 再按 `dist` 排序后在 DAG 上递推计数**——这就把它变成了
> [拓扑排序](topo.md) 的 DAG 上 DP。

---

## 6　Bellman-Ford 与负环

> Bellman-Ford 算法就是利用松弛操作：一开始只有 $dist[s] = 0$，其余均为 $\infty$。
> 然后枚举每条边，进行松弛操作。……
>
> 如果图中没有边权总和为负值的环（**负环**），那么最短路中每个点只会经过一次，
> 此时最短路中最多只会有 $n-1$ 条边。如果存在负环，
> 那么可以一直沿着负环无限走下去，每走一圈路径长度越短，因此不存在最短路。
>
> Bellman-Ford 算法每次更新成功时，都会使原来的最短路长度加 1。因此，
> **如果第 $n$ 次更新还有变动，则可以判定图中有负环**。否则更新次数不会超过 $n-1$ 次。
> 因此时间复杂度为 $O(nm)$。

```python
def bellman_ford(n, edges, s):
    """Bellman-Ford。edges = [(u, v, w), ...]。O(n*m)。

    返回 (dist, has_negative_cycle)。
    dist 用大整数 INF 而不是 float('inf')，这样 INF + w 仍是整数，
    比较不会因为 inf - inf 之类的怪事出问题。
    """
    INF = 1 << 60
    dist = [INF] * (n + 1)
    dist[s] = 0
    # 轮数的依据：无负环时最短路最多 n-1 条边，第 k 轮之后「最多 k 条边的最短路」已确定。
    # 所以 n-1 轮必然收敛；第 n 轮还能变小，只能是绕了负环。
    for it in range(n):                      # 跑 n 轮：第 n 轮还有更新就是负环
        changed = False
        for u, v, w in edges:                # 一轮 = 把所有边无差别松弛一次
            du = dist[u]
            if du < INF and du + w < dist[v]:   # du < INF：不可达的点不许往外传播
                dist[v] = du + w
                changed = True
        if not changed:                      # 提前收敛
            return dist, False               # 一整轮没有任何变化，后面也不会有
        if it == n - 1:                      # 第 n 轮仍在更新
            return dist, True                # 判据成立：存在 s 可达的负环
    return dist, False
```

> **`if du < INF` 这个判断不能省。** 不加的话，从「不可达点」出发的负权边
> 会把 `INF + (-5)` 当成一条更短的路，让不可达点的 `dist` 无意义地下降，
> 进而污染整张图。C++ 用 `0x3f3f3f3f` 就是为了让 `INF + INF` 不溢出，
> Python 没有溢出问题，但**逻辑上的污染仍然存在**。

**负环的三个易错点**：

| 问题 | 正确做法 |
| --- | --- |
| 「图中是否存在负环」 vs 「$s$ 能到达的负环」 | 前者要**把所有点的 `dist` 初始化为 0**（等价于建超级源点）；后者才从 $s$ 出发 |
| 不连通 | 上一条同理，从单点出发只能发现可达的负环 |
| 负权但**无负环**的最短路 | Bellman-Ford / SPFA 都正确；Dijkstra **错** |

---

## 7　SPFA：队列优化的 Bellman-Ford

> 实际上，每次更新有很多步骤是不必要的。如果上次更新时 $dist[x]$ 没有变动，
> 那么对于从 $x$ 出发的边就无需松弛。……
> 使用一个队列记录可以进行更新的点，初始时只有起点 $s$。当松弛边 $e$ 成功时，
> 就将 $v$ 加入队列。这个算法也被叫做 **SPFA**（Shortest Path Faster Algorithm）。
>
> 如果图中没有负环，那么更新的总次数不会比原始的 Bellman-Ford 算法多，
> 即时间复杂度上界依然为 $O(nm)$。

还有一句很诚实的话：

> 实际上，很多出题人都很懒，造的数据都是随机的，所以才有很多题目
> 即使 $n, m \approx 10^5$ 却也能跑过。

**这句话在今天已经不成立了**——「关于 SPFA，它死了」是竞赛圈的老梗，
现在的出题人默认会造反 SPFA 的网格数据。

```python
from collections import deque


def spfa(n, start, to, wt, s):
    """SPFA（队列优化 Bellman-Ford），支持负权。返回 (dist, has_neg_cycle)。

    最坏 O(n*m)。Python 下常数很大，能用 Dijkstra 就别用它。

    与 Bellman-Ford 的关系：Bellman-Ford 每轮盲扫所有边，而 dist 没变过的点
    再松弛它的出边也不会有新结果。SPFA 就用一个队列只保留「dist 刚刚变小」的点。
    """
    INF = 1 << 60
    dist = [INF] * (n + 1)
    dist[s] = 0
    inq = bytearray(n + 1)                   # inq[v] = 1 表示 v 此刻正在队列里
    inq[s] = 1
    cnt = [0] * (n + 1)                      # cnt[v] = v 被松弛的次数
    q = deque([s])
    while q:
        u = q.popleft()
        inq[u] = 0                           # 出队，之后再变小可以重新入队
        du = dist[u]
        for i in range(start[u], start[u + 1]):
            v = to[i]
            nd = du + wt[i]
            if nd < dist[v]:                 # v 变小了 -> 它的出边需要重新松弛
                dist[v] = nd
                if not inq[v]:               # ★ 已在队列里就别重复入队
                    cnt[v] += 1
                    if cnt[v] >= n:          # 入队 n 次 -> 有负环
                        return dist, True    # 判据同 Bellman-Ford：最短路不会有 n 条边
                    inq[v] = 1
                    q.append(v)
    return dist, False                       # 队列自然排空 = 再没有可松弛的边
```

### SLF 优化（Small Label First）

常见模板用的就是这个（`deque` + 队首比较）：

```cpp
if (!f[v]) {
    f[v] = 1;
    if (q.empty() || dist[v] > dist[q.front()]) q.push_back(v);
    else q.push_front(v);
}
```

**思想**：如果新入队点的 `dist` 比队首还小，就把它插到队首——
让「更有希望」的点先被处理，减少无效松弛。Python 版：

```python
# [片段] SLF：把上面 spfa 的入队部分换成这段
inq[v] = 1
if q and dist[v] < dist[q[0]]:               # q[0] 是当前队首，O(1) 取到
    q.appendleft(v)                          # 比队首还小 -> 插队首，让它先被松弛
else:
    q.append(v)                              # 否则老实排队尾（退化成普通 SPFA）
```

| 优化 | 思想 | 效果 |
| --- | --- | --- |
| **SLF** | `dist` 比队首小就插队首 | 随机数据下快 15%–30%，**仍可被卡** |
| LLL（Large Label Last） | 队首 `dist` 大于队内平均值就轮转到队尾 | 需要维护队内和，Python 下**得不偿失** |
| SLF + 计数限制 | 每个点插队首的次数上限 | 防止被专门构造的数据卡死 |

> **Python 选手的 SPFA 使用守则**：
> 1. **边权非负 → 一律 Dijkstra**，不要碰 SPFA；
> 2. 有负权且 $nm \le 10^6$（比如 $n \le 1000$、$m \le 10^4$）→ 可以用 SPFA；
> 3. 有负权且规模更大 → 考虑「Johnson 重赋权 + Dijkstra」或者干脆重新想模型；
> 4. **只判负环**（不求最短路）→ 用 **DFS 版 SPFA**（找到「当前栈上重复点」立刻返回），
>    通常比 BFS 版快一个数量级，但要写成迭代。

### SPFA 求最短路条数

有一个精妙的两数组做法：

> 考虑定义两个数组 `F[x]`、`Sf[x]`，分别表示到 $x$ 点**能传递**的最短路方案数、
> 到 $x$ 点的最短路方案数。……在队列中的话，那么其能传递的方案数并没有累加给其他点，
> 所以要留着；不在队列中的话，那么它之前能传递的方案数已经累加给其他点了，
> 那么就直接覆盖。

为什么要两个数组？因为**一个点可能被反复松弛**，如果只用一个计数器，
「已经传递出去的方案数」会被重复累加。Python 版：

```python
def spfa_count(n, start, to, wt, s, MOD=10 ** 9 + 7):
    """SPFA 同时求最短路长度与最短路条数。

    F[x] = x 身上「还没传递出去」的方案数（传出去之后清零）；
    S[x] = 到 x 的最短路总条数（最终答案）。
    """
    INF = 1 << 60
    dist = [INF] * (n + 1)
    F = [0] * (n + 1)
    S = [0] * (n + 1)
    dist[s] = 0
    F[s] = S[s] = 1                          # 起点自己算一条「空路径」
    inq = bytearray(n + 1)
    inq[s] = 1
    q = deque([s])
    while q:
        u = q.popleft()
        inq[u] = 0
        fu = F[u]                            # 取走待传递的方案数
        F[u] = 0                             # ★ 这批方案数即将传递出去，先清零
        if fu == 0:
            continue                         # 没有新增方案，无需再传播
        du = dist[u]
        for i in range(start[u], start[u + 1]):
            v = to[i]
            nd = du + wt[i]
            if nd < dist[v]:                 # 找到更短的路 -> 计数全部作废重来
                dist[v] = nd
                F[v] = fu                    # 直接覆盖，不是累加
                S[v] = fu
                if not inq[v]:
                    inq[v] = 1
                    q.append(v)
            elif nd == dist[v]:              # 同样长 -> 方案数累加
                F[v] = (F[v] + fu) % MOD     # 取模放在每次累加处，数值不会膨胀
                S[v] = (S[v] + fu) % MOD
                if not inq[v]:
                    inq[v] = 1
                    q.append(v)
    return dist, S                           # F 最终会全部清零，S 才是答案
```

> **为什么 `F[u] = 0` 是关键？** 因为 $u$ 可能被再次松弛后重新入队。
> 若不清零，第二次出队时会把「上一批已经传出去的方案数」再传一遍，
> 结果偏大。

---

## 8　Floyd：全源最短路

> Floyd 算法直接采用邻接矩阵记录原图 $G$，用矩阵 $W$ 表示点对间的最短路。
> $G$ 相当于不经过任何中介点的最短路矩阵，于是 Floyd 算法尝试不断加入中介点来更新最短路矩阵。
>
> 从 1 开始枚举新加入的中介点 $k$，对于任意两个点 $i$ 和 $j$，其最短路有两种选择：
> 一是保持原样，即 $W[i][j]$；二是经过新的中介点 $k$，即 $W[i][k] + W[k][j]$。两者取最小值即可。

```text
for k in [1..n]:
    for i in [1..n]:
        for j in [1..n]:
            W[i][j] = min(W[i][j], W[i][k] + W[k][j])
```

> ⚠️ **三重循环的顺序必须是 $k$ 在最外层**。写成 `i,j,k` 的顺序是**错的**——
> 那样 $W[i][k]$ 在被用到时还没算完。这是 Floyd 唯一但也是最致命的坑。
> 记忆法：$k$ 是「允许中转的点集是 $\{1..k\}$」这个 DP 维度，
> 必须一层层放开，所以在最外面。

### Python 版：把内层循环下沉到 C 层

朴素三重循环在 Python 下的代价：$n = 100$ 是 $10^6$ 次（约 0.5 秒，可接受），
$n = 200$ 是 $8\times10^6$ 次（约 4 秒，超时）。

**优化的核心是消灭最内层的 $j$ 循环**，用 `map(min, ...)` 让整行比较落到 C 层：

```python
def floyd(g, n):
    """Floyd 全源最短路。g 是 (n+1)x(n+1) 的邻接矩阵（就地修改）。

    关键优化：内层 j 循环用 map(min, 行, 行) 下沉到 C 层。
    ★ INF 必须用**大整数**而不是 float('inf')：
      int.__add__(float) 返回 NotImplemented，map(dik.__add__, ...) 会崩。
    """
    for k in range(1, n + 1):                # k 必须在最外层：它是 DP 的「允许中转点集」维度
        gk = g[k]                            # 第 k 行，绑成局部名
        for i in range(1, n + 1):
            gi = g[i]
            dik = gi[k]                      # i 到 k 的当前最短路
            if dik >= (1 << 60):             # ★ i 到 k 不可达，整行跳过
                continue                     # 经过 k 中转不可能更优，省掉一整行运算
            # 等价于 for j: gi[j] = min(gi[j], dik + gk[j])
            # 内层 map 把 gk 整行加上 dik，外层 map 与原行逐格取 min
            gi[:] = list(map(min, gi, map(dik.__add__, gk)))   # 切片赋值 = 就地覆盖整行
    return g
```

| 写法 | $n = 200$ 实测 | 说明 |
| --- | --- | --- |
| 三重 `for` + 下标 | ~5 秒 | $8\times10^6$ 次 Python 层迭代 |
| 内层改列表推导式 | ~2.5 秒 | 少了字节码调度开销 |
| **`map(min, gi, map(dik.__add__, gk))`** | **~0.8 秒** | 循环整个在 C 层 |
| 再加 `if dik >= INF: continue` | **~0.5 秒** | 稀疏图上能跳掉大量整行 |

> **Python 下 Floyd 的现实上限**：朴素写法 $n \le 100$，
> 切片 / `map` 优化后 $n \le 250$ 左右。
> **$n \ge 300$ 就该换成「跑 $n$ 次 Dijkstra」**（$O(nm\log m)$，稀疏图上更快）。

### Floyd 判最小环

Floyd 判最小环的经典模板：

```cpp
for (int k = 1; k <= n; k++) {
    for (int i = 1; i < k; i++)              // 最小环
        for (int j = i+1; j < k; j++)
            ans = min(ans, g[i][j] + w[i][k] + w[k][j]);
    for (int i = 1; i <= n; i++)             // Floyd
        for (int j = 1; j <= n; j++)
            if (i != j) g[i][j] = min(g[i][j], g[i][k] + g[k][j]);
}
```

**原理**：枚举环上**编号最大的点** $k$，以及环上与 $k$ 相邻的两个点 $i, j$。
此时 $i \to j$ 的路径只允许经过编号 $< k$ 的点——**这恰好就是 Floyd 做完前 $k-1$ 轮后的 $g[i][j]$**。
所以「先统计答案，再做第 $k$ 轮松弛」的顺序不能颠倒。

```python
def floyd_min_cycle(w, n):
    """Floyd 求无向图最小环（环长 >= 3）。O(n^3)。

    w 是原始邻接矩阵（不会被修改），g 是最短路矩阵（会被就地更新）。
    返回最小环长；不存在返回 None。
    """
    INF = 1 << 60
    g = [row[:] for row in w]                # g 会被 Floyd 改，w 保持原始边权
    ans = INF
    for k in range(1, n + 1):
        wk = w[k]                            # k 的原始边权一行
        # ---- 第一步：统计以 k 为「编号最大点」的环 ----
        # 此时 g[i][j] 只用到了编号 < k 的中转点，正是需要的
        for i in range(1, k):                # i < k：环上与 k 相邻的一端
            wik = wk[i]
            if wik >= INF:
                continue                     # k 与 i 之间没有直接边，构不成环
            gi = g[i]
            for j in range(i + 1, k):        # j > i，避免同一个环算两次
                t = gi[j] + wik + wk[j]      # 环 = i..j 的最短路 + 边 j-k + 边 k-i
                if t < ans:
                    ans = t
        # ---- 第二步：把 k 作为中转点做 Floyd 松弛 ----
        # 顺序不能颠倒：先松弛的话 g[i][j] 就会用上 k，环会退化成走回头路
        gk = g[k]
        for i in range(1, n + 1):
            gi = g[i]
            dik = gi[k]
            if dik >= INF:
                continue                     # i 到 k 不可达，整行跳过
            gi[:] = list(map(min, gi, map(dik.__add__, gk)))
    return None if ans >= INF else ans       # ans 没被改过 = 图上没有长度 >= 3 的环
```

> **两个必须记住的细节**：
> 1. **`w` 和 `g` 必须是两个矩阵**：环上与 $k$ 相邻的两条边要用**原始边权** `w`，
>    而 $i \to j$ 那一段要用**最短路** `g`。混用会得到「重复经过某条边」的假环；
> 2. **`j` 从 `i+1` 开始**：$i, j$ 互换是同一个环，从 `i+1` 起可以避免算两遍，
>    也顺便避开了 $i = j$ 时权值出错的情况。

### Floyd 的其他用途

| 用途 | 改动 |
| --- | --- |
| **传递闭包**（可达性） | <code>W[i][j] &#124;= W[i][k] &amp; W[k][j]</code>，用 Python 大整数当位图可以整行并行 |
| **最短路条数** | 再维护矩阵 $C$：`==` 时 `C[i][j] += C[i][k]*C[k][j]`，`<` 时直接赋值 |
| **最小瓶颈路** | `W[i][j] = min(W[i][j], max(W[i][k], W[k][j]))` |
| **判负环** | 跑完看是否存在 `W[i][i] < 0` |
| **「重要的城市」** | 若存在 $i,j$ 使 $W[i][k]+W[k][j] = W[i][j]$ 且 $C[i][j] = C[i][k]\cdot C[k][j]$，则 $k$ 重要 |

> **传递闭包的 Python 杀手锏**：把每一行压成一个**大整数位图**，
> 则 `reach[i] |= reach[k]`（当第 $k$ 位为 1 时）一句话完成整行的 $O(n)$ 或运算，
> 整个算法降到 $O(n^2)$ 次大整数操作。$n = 2000$ 都能过。
> 见 [位运算](../basic/bit.md)。

---

## 9　建图技巧：真正的难点

模板题只考「会不会写 Dijkstra」，真正的题考「**怎么把问题变成图**」。

| 技巧 | 什么时候用 | 例子 |
| --- | --- | --- |
| **反图** | 「所有点到某一个点的最短路」 | **BISHI109**；P2296 |
| **拆点** | 一个点有多种「状态」 | **BISHI108**（站台 / 车上）；Steam Roller（横向 / 纵向） |
| **虚拟源点** | 多个起点 / 起点有初始代价 | 建一个超级源连向所有起点 |
| **虚拟链** | 一条线路上任意两点连边会爆边数 | **BISHI108**：$O(s^2)$ 降到 $O(s)$ |
| **分层图** | 「最多免费 $k$ 条边」 | 建 $k+1$ 层，层间边权 0 |
| **边转点** | 限制发生在「边」上 | 把每条边变成一个点 |

### 反图

```python
# [片段] 反图：把每条 u->v 换成 v->u 重新建一次表
start_r, to_r, wt_r = build_csr_weighted(n, vs, us, ws)   # ★ us 和 vs 交换
rdist = dijkstra(n, start_r, to_r, wt_r, s)               # rdist[v] == 原图 v->s 的最短路
```

> **一句话**：在反图上从 $s$ 出发的单源最短路，就是原图上「所有点到 $s$」的最短路。
> 这把 $n$ 次 Dijkstra 变成 1 次。BISHI109 全靠这一招。

### 拆点 + 虚拟链（BISHI108 的核心）

一条巴士线路经过 $s$ 个站，要表达「在任意站上车、在之后任意站下车」：

| 建法 | 边数 | $M=100, s=500$ 时 |
| --- | --- | --- |
| 前面的站 → 后面的站，各连一条 | $O(s^2)$ | $1.25\times10^7$，Python 建图就跪 |
| **给每个位置建「车上」节点 $R_i$，串成链** | $O(s)$ | $1.5\times10^5$，轻松 |

```text
站台 t_i  --权 1-->  R_i        （上车，算一趟车）
R_i      --权 0-->  R_{i+1}     （继续往前开，免费；天然保证只能顺向）
R_i      --权 0-->  站台 t_i    （下车，免费）
```

**边权只有 0 和 1 → 直接上 0-1 BFS**，连堆都省了。

---

## 10　例题

<!-- CHAPTER-EXAMPLE-TABLE -->

### BISHI105 【模板】单源最短路Ⅰ ‖ 无权图：BFS（中等）

> $n, m \le 2\times10^5$ 的**有向无权图**（可能不连通、可能有重边，无自环），
> 输出从 $s$ 到所有点的最短路径长度，不可达输出 $-1$。
> 时限：C/C++ 5 秒，其他语言 10 秒。
> 题面见 [原题](https://www.nowcoder.com/practice/359e14832ce1476fadc70dd4bc36b991)。
> 题解见 [`solutions/nowcoder/BISHI105/sol.py`](../solutions/BISHI105.md)（已用官方样例验证）。

**这题的全部考点就是「认出无权图该用 BFS」**。上 Dijkstra 也能过
（时限给到 10 秒），但那是白白多花 5 倍时间。

```python
import sys
from collections import deque


def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); m = int(data[1]); s = int(data[2])

    # ---- CSR 邻接表（有向）：数度数 -> 前缀和 -> 回填 ----
    deg = [0] * (n + 2)                      # 第一趟：数出度
    for i in range(3, 3 + 2 * m, 2):         # 只数出边，有向图不加反向
        deg[int(data[i])] += 1               # 边数据从下标 3 开始，每条边占 2 个 token
    start = [0] * (n + 2)                    # 第二趟：出度前缀和 -> 每个点的起始下标
    acc = 0
    for i in range(1, n + 1):
        start[i] = acc                       # acc = 1..i-1 的出度之和
        acc += deg[i]
    start[n + 1] = acc                       # 哨兵，同时是 adj 的总长度（有向图即 m）
    pos = start[:]                           # 第三趟用的游标，start 保持不动
    adj = [0] * acc
    p = 3
    for _ in range(m):
        u = int(data[p]); v = int(data[p + 1]); p += 2
        adj[pos[u]] = v                      # 写到 u 的下一个空位
        pos[u] += 1                          # 游标右移

    dist = [-1] * (n + 1)                    # -1 既是未访问标记，也是最终输出值
    dist[s] = 0
    q = deque([s])                           # 必须 deque
    while q:
        u = q.popleft()                      # 队列距离单调不减，队头已是最短
        d = dist[u] + 1                      # 无权图：往外走一条边就是 +1
        for i in range(start[u], start[u + 1]):
            v = adj[i]
            if dist[v] < 0:                  # 只处理首次到达，重边天然被跳过
                dist[v] = d
                q.append(v)
    sys.stdout.write(" ".join(map(str, dist[1:])) + "\n")   # 下标 0 是占位，不输出


main()
```

**四个工程要点**：

| 要点 | 理由 |
| --- | --- |
| `deque` 而不是 `list.pop(0)` | 后者 $O(n)$，$2\times10^5$ 会退化成 $4\times10^{10}$ |
| **CSR** 而不是 `[[] for _ in ...]` | $2\times10^5$ 个 list 对象光对象头就十几 MB |
| `dist` 初值 $-1$ | 一个数组身兼「访问标记 + 距离 + 不可达输出值」三职 |
| 输出一次 `join` | $2\times10^5$ 个数字，逐个 `print` 会被 IO 拖垮 |

**三个坑**：

1. 图是**有向**的，建表只加 $u \to v$，别顺手加反向；
2. 有**重边**（样例 1 里 `4->3` 出现了两次），BFS 天然免疫——第二次看到时
   `dist[v]` 已经填过了；
3. `dist[s] = 0` 要在入队**之前**设好。

> **能不能用 `list` 当队列 + 头指针？** 能，而且更快：
> `q = [s]; head = 0; while head < len(q): u = q[head]; head += 1`。
> 代价是队列会一直增长（不释放已出队元素），$2\times10^5$ 个点无所谓。
> 见 [BFS广度优先搜索](../search/bfs.md)。

### BISHI106 【模板】单源最短路Ⅲ ‖ 非负权图：Dijkstra（较难）

> $n, m \le 2\times10^5$ 的**有向非负权图**（$0 \le w \le 10^9$，可能不连通、可能有重边）。
> 输出从 $s$ 到所有点的最短路，不可达输出 $-1$。
> 时限：C/C++ 5 秒，其他语言 10 秒。
> 题面见 [原题](https://www.nowcoder.com/practice/d7fafd4f3340439e90597532850257b5)。
> 题解见 [`solutions/nowcoder/BISHI106/sol.py`](../solutions/BISHI106.md)（已用官方样例验证）。

标准的堆优化 Dijkstra + 懒删除 + CSR：

```python
import sys
from heapq import heappush, heappop


def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); m = int(data[1]); s = int(data[2])

    # ---- CSR 邻接表（有向带权，三个扁平数组）：数度数 -> 前缀和 -> 回填 ----
    deg = [0] * (n + 2)                      # 第一趟：数出度
    for i in range(3, 3 + 3 * m, 3):         # 每条边占 3 个 token，起点在每组的第一个
        deg[int(data[i])] += 1
    start = [0] * (n + 2)                    # 第二趟：前缀和定出每个点的起始下标
    acc = 0
    for i in range(1, n + 1):
        start[i] = acc
        acc += deg[i]
    start[n + 1] = acc                       # 哨兵；遍历 u 时用 start[u+1] 当右界
    pos = start[:]                           # 第三趟用的游标
    to = [0] * acc                           # to[i] 与 wt[i] 严格对齐，同一个 i 是同一条边
    wt = [0] * acc
    p = 3
    for _ in range(m):
        u = int(data[p]); v = int(data[p + 1]); w = int(data[p + 2]); p += 3
        k = pos[u]                           # u 的下一个空位
        to[k] = v; wt[k] = w
        pos[u] = k + 1                       # 游标右移

    INF = float("inf")                       # 只做比较不做加法，这里用 inf 安全
    dist = [INF] * (n + 1)
    dist[s] = 0
    heap = [(0, s)]                          # (距离, 点号)；元组比较先比距离
    while heap:
        d, u = heappop(heap)                 # 全堆最小 -> 非负权保证 u 已定型
        if d > dist[u]:                      # 懒删除：过期记录直接丢掉
            continue                         # 不写这行，点会被重复展开，大数据必 TLE
        for i in range(start[u], start[u + 1]):
            v = to[i]
            nd = d + wt[i]
            if nd < dist[v]:                 # 严格小于：0 权边不会引发自我松弛
                dist[v] = nd
                heappush(heap, (nd, v))      # 不改旧记录，只押一份新的进堆

    out = [(str(x) if x != INF else "-1") for x in dist[1:]]   # 没被松弛过 = 不可达
    sys.stdout.write(" ".join(out) + "\n")


main()
```

**复杂度**：$O(m \log m)$，$m = 2\times10^5$ 时约 $2\times10^5 \times 18 = 3.6\times10^6$ 次堆操作。
Python 下大约 2–4 秒，10 秒时限**能过但不宽裕**。

**四个坑**：

1. **边权可以是 0**（样例 1 里 `1->4` 权 0，答案 `dist[4] = 1` 走的是 `2->1->4`）。
   0 权对 Dijkstra 完全没问题，但要注意别写成 `if nd <= dist[v]`——
   那会让 0 权边无限自我松弛；
2. 图**有向**、可能**不连通**（输出 $-1$）、可能有**重边**；
3. **边权和最大 $2\times10^5 \times 10^9 = 2\times10^{14}$**，C++ 必须 `long long`，
   Python 的整数无限精度，白送（见 [高精度与大整数](../toolkit/bignum.md)）；
4. 起点自己输出 0。

> **这里为什么可以用 `float("inf")`？** 因为只做 `nd < dist[v]` 的比较，
> `int < float('inf')` 永远为真，没有 `int + float('inf')` 的运算。
> 但 **Floyd 里不行**（要算 `INF + INF`），那里必须用大整数。
> 保险起见，**统一用 `1 << 60` 当 INF 是个好习惯**。

> **Python 现实性判断**：$m\log m \approx 3.6\times10^6$ 次堆操作，
> 每次 `heappush` 要建一个元组并做 $\log$ 次比较。10 秒时限下应该能过。
> 若 TLE，可尝试的手段依次是：
> ① 把 `(d, v)` 编码成单个整数 `d * (n+1) + v`（省掉元组构造，
> 前提是 `d` 不会溢出到影响低位——本题 $d \le 2\times10^{14}$、$n+1 \le 2\times10^5$，
> Python 大整数扛得住）；② 把 `heappush`/`heappop` 绑成局部名；
> ③ 检查是不是误用了 `defaultdict`。

### BISHI108 最优乘车（简单）

> $M \le 100$ 条**单向**巴士线路，$N \le 500$ 个站。每条线路给出依次经过的站点序列。
> 求从 $1$ 号站到 $N$ 号站的**最少换乘次数**；到不了输出 `NO`。
> 题面见 [原题](https://www.nowcoder.com/practice/83101a4f624042b59a629089e83b6dd1)。
> 题解见 [`solutions/nowcoder/BISHI108/sol.py`](../solutions/BISHI108.md)（已用官方样例验证）。

**建图题**，算法本身只有 0-1 BFS 十几行。

「最少换乘次数 = 最少乘车段数 $- 1$」。朴素建法是「同一线路上前面的站 → 后面的站」
各连一条权 1 的边，但一条 $s$ 站的线路要连 $s^2/2$ 条边，
$100 \times 500$ 就是 $1.25\times10^7$ 条，Python 建图直接跪。

**拆点建虚拟链**（§9 讲的技巧），边数降到 $O(\sum s) \approx 1.5\times10^5$：

```python
import sys
from collections import deque


def main():
    data = sys.stdin.buffer.read().split()
    M = int(data[0]); N = int(data[1])        # ★ 注意是 M 在前、N 在后

    lines = []
    p = 2
    total_stops = 0                           # 所有线路的站点数之和，决定虚拟点的个数
    for _ in range(M):
        s = int(data[p]); p += 1              # 这条线路有 s 个站
        stops = [int(v) for v in data[p:p + s]]; p += s
        lines.append(stops)
        total_stops += s

    # 节点编号：1..N 是站台，N+1.. 是各线路各位置的「车上」节点
    V = N + total_stops + 1                   # +1 是因为下标 0 空着不用
    adj = [[] for _ in range(V)]
    nid = N + 1                               # 下一个可用的虚拟点编号
    for stops in lines:
        base = nid                            # 这条线路的虚拟点从 base 开始连续编号
        s = len(stops)
        for i, st in enumerate(stops):
            r = base + i                      # 「坐着这条线路、正停在第 i 站」这个状态
            adj[st].append((r, 1))            # 上车：算一趟车，权 1
            adj[r].append((st, 0))            # 下车：免费，权 0
            if i + 1 < s:
                adj[r].append((r + 1, 0))     # 继续往前开：免费，且只能顺向
                                              # 链上只有 i -> i+1 一个方向，天然禁止倒坐
        nid += s                              # 让下一条线路的虚拟点接着往后排

    INF = float("inf")
    dist = [INF] * V                          # dist[x] = 到达状态 x 至少要坐几趟车
    dist[1] = 0                               # 从 1 号站台出发，还没上车
    dq = deque([(0, 1)])                      # 0-1 BFS 必须用双端队列
    while dq:
        d, u = dq.popleft()
        if d > dist[u]:                       # 懒删除，过期记录跳过
            continue                          # 0-1 BFS 里一个点可能被多次入队
        for v, w in adj[u]:
            nd = d + w
            if nd < dist[v]:                  # 判据是「变小了」，不是「没访问过」
                dist[v] = nd
                if w:
                    dq.append((nd, v))        # 权 1 放队尾
                else:
                    dq.appendleft((nd, v))    # 权 0 放队首，保持队内距离单调不减
    d = dist[N]                               # 到 N 号站台一共坐了 d 趟车
    sys.stdout.write("NO\n" if d == INF else "%d\n" % (d - 1))   # 换乘次数 = 趟数 - 1


main()
```

**虚拟链为什么天然保证「不能倒着坐」**：链上的边只有 $R_i \to R_{i+1}$ 一个方向。
在位置 $i$ 上车后，只能沿链往后走，走到 $R_j$（$j > i$）再下车。
这正是「单向巴士」的语义，**一条边都不用多加**。

**四个坑**：

1. 输入第一行是 **$M$（线路数）在前、$N$（站数）在后**，读反了全盘皆输；
2. 答案是「乘车段数 $- 1$」，无需换乘时输出 `0`；
3. 到不了输出 `NO`（大写）；
4. 0-1 BFS 的队列**必须是 `deque`**——`list` 没有 $O(1)$ 的头插。

> **为什么不用 Dijkstra？** 用也对，但 0-1 BFS 是 $O(V+E)$、无堆、无 $\log$。
> 在 Python 里省掉 `heapq` 的元组构造和上浮下沉，实测快 2–3 倍。
> **边权只有 0 和 1 就上 0-1 BFS**，这是条硬规则。

### BISHI109 邮递员送信（中等）

> $n \le 10^3$ 个路口、$m \le 10^5$ 条**单向**道路（$1 \le w \le 10^4$），保证任意两点互相可达。
> 邮递员从 $1$ 号出发，每次送一件包裹到某个点后**必须返回 $1$ 号**再取下一件。
> 求送完 $2..n$ 全部 $n-1$ 件的最短总时间。
> 题面见 [原题](https://www.nowcoder.com/practice/2b0c636cf77d441fa96d40ac64290d39)。
> 题解见 [`solutions/nowcoder/BISHI109/sol.py`](../solutions/BISHI109.md)（已用官方样例验证）。

答案是 $\sum_{v=2}^{n} \bigl(d(1 \to v) + d(v \to 1)\bigr)$。

- **去程** $d(1 \to v)$：原图上从 1 跑一次 Dijkstra，一次搞定；
- **回程** $d(v \to 1)$：逐点跑就是 $n$ 次 Dijkstra（$n=1000$、$m=10^5$ 时约 $10^8$ 级，必挂）。
  **正确做法是把所有边反向建图，在反图上从 1 跑一次 Dijkstra**，
  得到的 `rdist[v]` 恰好就是原图里 $v \to 1$ 的最短路。

**两次 Dijkstra 解决全部问题。**

```python
import sys
from heapq import heappush, heappop


def build_csr(n, us, vs, ws):
    """把边表压成 CSR：返回 (start, to, wt)。O(n + m)。有向图，只加 us -> vs。"""
    m = len(us)
    deg = [0] * (n + 2)                      # 第一趟：数出度
    for u in us:
        deg[u] += 1
    start = [0] * (n + 2)                    # 第二趟：前缀和 -> 每个点的起始下标
    acc = 0
    for i in range(1, n + 1):
        start[i] = acc
        acc += deg[i]
    start[n + 1] = acc                       # 哨兵，也是 to / wt 的长度
    pos = start[:]                           # 第三趟用的游标
    to = [0] * acc
    wt = [0] * acc
    for i in range(m):
        u = us[i]
        k = pos[u]                           # u 的下一个空位
        to[k] = vs[i]; wt[k] = ws[i]         # 终点与边权写在同一个下标上
        pos[u] = k + 1
    return start, to, wt


def dijkstra(n, start, to, wt, src):
    """堆优化 Dijkstra + 懒删除。O(m log m)。"""
    INF = float("inf")
    dist = [INF] * (n + 1)
    dist[src] = 0
    heap = [(0, src)]
    while heap:
        d, u = heappop(heap)                 # 取出当前最小距离的候选
        if d > dist[u]:                      # 懒删除
            continue                         # u 已被更小的距离定型，这份是旧账
        for i in range(start[u], start[u + 1]):
            v = to[i]
            nd = d + wt[i]
            if nd < dist[v]:
                dist[v] = nd
                heappush(heap, (nd, v))      # 代替 decrease-key：多押一份新记录
    return dist


def main():
    data = sys.stdin.buffer.read().split()
    n, m = int(data[0]), int(data[1])
    us = [0] * m; vs = [0] * m; ws = [0] * m   # 预分配三个等长数组，避免 append 扩容
    p = 2
    for i in range(m):
        us[i] = int(data[p]); vs[i] = int(data[p + 1]); ws[i] = int(data[p + 2])
        p += 3

    d1 = dijkstra(n, *build_csr(n, us, vs, ws), src=1)   # 去程：1 -> v
    d2 = dijkstra(n, *build_csr(n, vs, us, ws), src=1)   # 回程：反图上 1 -> v 即 v -> 1
                                                         # 只把 us / vs 换个位置就是反图

    total = 0
    for v in range(2, n + 1):                # 1 号点自己不用送，从 2 开始累加
        total += d1[v] + d2[v]               # 每件包裹 = 去一趟 + 回一趟
    sys.stdout.write("%d\n" % total)


main()
```

**`build_csr(n, vs, us, ws)` 就是反图**——把 `us` 和 `vs` 交换个位置，
同一份构建代码复用两次。这比手写第二份建图代码更不容易出错。

**四个坑**：

1. **道路是单向的**，反图必须真的重新建表，不能复用原图；
2. 可能有**重边**（样例里 `3->5` 出现两次，权都是 6），Dijkstra 天然处理；
3. 答案可达 $10^3 \times 2 \times 10^7 = 2\times10^{10}$ 级别，C++ 要 `long long`，**Python 无忧**；
4. 题面保证互相可达，所以不会出现 `INF`；但代码仍按 `INF` 处理更稳。

> **$n$ 只有 1000，为什么不用朴素 $O(n^2)$ Dijkstra？**
> 可以，$10^6$ 次迭代 Python 下约 0.5 秒。但 $m$ 到 $10^5$ 时堆优化是
> $10^5 \times 17 \approx 1.7\times10^6$，同量级且**是通用写法**。
> 建议无脑用堆优化版，少记一套代码。

> **这题也可以用 Floyd 吗？** $n = 1000$ 时 Floyd 是 $10^9$ 次操作，
> C++ 都要好几秒，Python 绝无可能。**看到「$n$ 上千」就把 Floyd 排除掉。**

---

## 11　本章速查

| 判断 | 结论 |
| --- | --- |
| 无权图 | **BFS**，$O(n+m)$，别上 Dijkstra |
| 边权 0/1 | **0-1 BFS**（`deque` 两端插入），比 Dijkstra 快 2–3 倍 |
| 非负权单源 | **Dijkstra + `heapq` 懒删除** |
| 稠密图 + $n \le 2000$ | 朴素 $O(n^2)$ Dijkstra |
| 有负权 | Bellman-Ford / SPFA，$O(nm)$ |
| 判负环 | 松弛 $n$ 轮仍变动 / 某点入队 $\ge n$ 次 |
| 全源 + $n \le 100$ | **Floyd**（Python 优化后可到 250） |
| 全源 + $n$ 上千 | 跑 $n$ 次 Dijkstra，**Floyd 直接排除** |
| 所有点 → 某点 | **反图跑一次单源** |

| 陷阱 | 说明 |
| --- | --- |
| **Dijkstra 遇负权** | **算法本身就错**，不是常数问题 |
| 懒删除漏写 `if d > dist[u]` | 点被重复展开，大数据必 TLE |
| Floyd 循环顺序 | **$k$ 必须在最外层** |
| Floyd 的 INF | 用**大整数**不用 `float('inf')`（要做 `INF + INF`） |
| 邻接矩阵重边 | 必须 `min`，不能直接赋值 |
| Bellman-Ford | 松弛前判 `dist[u] < INF`，否则污染不可达点 |
| 「图中有负环」vs「$s$ 可达的负环」 | 前者要把所有 `dist` 初始化为 0 |
| 最短路计数遇 0 权边 | Dijkstra 边松弛边计数会算错，改用 DAG 递推 |
| Floyd 最小环 | `w` 与 `g` 两个矩阵不能混用；`j` 从 `i+1` 起 |

| Python 特有 | 做法 |
| --- | --- |
| 邻接表 | **CSR**（$n \ge 2\times10^5$）或定长 `list of list`；**禁用 `defaultdict`** |
| 堆 | `heapq` + 元组 `(d, v)`；不要自定义类 |
| decrease-key | 没有，**用懒删除代替** |
| Floyd 内层循环 | `map(min, gi, map(dik.__add__, gk))` 下沉到 C 层，快 5 倍 |
| SPFA | **常数很大，有 Dijkstra 就别用** |
| 大整数 | 边权和不会溢出，C++ 要 `long long` 的地方 Python 白送 |

| 建图技巧 ← 触发词 |
| --- |
| **反图** ← 「所有点到某点」 |
| **拆点** ← 一个点有多种状态（方向 / 是否在车上 / 剩余次数） |
| **虚拟链** ← 「同一组内任意前 → 后」，避免 $O(s^2)$ 建边 |
| **分层图** ← 「最多免费 $k$ 次」 |
| **虚拟源点** ← 多起点 / 起点带初始代价 |
| **0-1 权** ← 「最少换乘 / 最少打破 / 最少转弯」 |

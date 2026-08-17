# 第 61 章　BFS 广度优先搜索

> **配套例题**：BISHI80 走迷宫、BISHI81 剪纸游戏、BISHI82 没挡住洪水、BISHI83 迷宫问题、BISHI84 时津风的资源收集、BISHI97 旺仔哥哥走迷宫、BISHI101 世界树上找米库（多源 BFS）、BISHI105 【模板】单源最短路Ⅰ
> **来源**：S3 day7《简单图论》图的遍历、最短路
> **前置**：[33-队列与双端队列](../part3-数据结构/33-队列与双端队列.md)、[60-DFS深度优先搜索](60-DFS深度优先搜索.md)

BFS（Breadth First Search，广度优先搜索）是「**一层一层地铺开**」。

它和 DFS 的唯一结构差别是**把栈换成队列**，但换来一条 DFS 永远给不了的性质：

> **在边权全为 1 的图上，BFS 第一次访问到某个点时的层号，就是从起点到它的最短距离。**

这条性质让 BFS 成为「最少步数」类问题的标准答案。
而且对 Python 来说还有一个巨大的附加好处：
**BFS 天然是迭代的，永远不会爆栈**——这是它在 Python 里比 DFS 更受欢迎的现实原因。

---

## 61.1　基本框架与正确性

```python
from collections import deque


def bfs(s, adj, n):
    """无权图单源最短路。dist[v] = -1 表示不可达。O(n + m)。"""
    dist = [-1] * n
    dist[s] = 0
    q = deque([s])                       # ★ 必须是 deque
    while q:
        u = q.popleft()
        d = dist[u] + 1
        for v in adj[u]:
            if dist[v] < 0:              # 第一次访问 = 最短
                dist[v] = d
                q.append(v)
    return dist
```

**为什么第一次访问就是最短？** 因为队列里的元素**距离单调不减**：
队首距离为 $d$ 的点扩展出的新点距离都是 $d+1$，而队列中已有的点距离只可能是 $d$ 或 $d+1$。
所以出队顺序天然是按层的，任何一个点第一次被塞进队列时拿到的都是最小的层号。

> ⚠️ **标记必须在「入队时」做，不能在「出队时」做。**
> 出队才标记的话，同一个点会被它的多个邻居重复入队，
> 队列规模从 $O(n)$ 膨胀到 $O(m)$，最坏情况直接 TLE 甚至 MLE。
> 这条和 DFS 的「入栈即标记」是同一条规则。

### `dist` 数组一身兼三职

```python
dist = [-1] * n        # -1 既是「未访问」标记，又是「不可达」的输出值
```

这是竞赛里的标准写法：省掉一个 `vis` 数组，少一次数组访问，
而且 BFS 结束后直接输出 `dist` 就完事了（不可达的位置正好是 $-1$）。

### DFS vs BFS 对照

| | DFS | BFS |
| --- | --- | --- |
| 容器 | 栈（`list`） | **队列（`deque`）** |
| 递归形态 | 天然递归 | **天然迭代** |
| Python 爆栈风险 | ⚠️ 有（见 [60.4](60-DFS深度优先搜索.md#604-递归改迭代)） | ✅ **完全没有** |
| 无权最短路 | ❌ 不保证 | ✅ **保证** |
| 内存峰值 | $O(\text{深度})$ | $O(\text{最宽一层})$ |
| 求所有方案 | ✅ 回溯 | ❌ 不适合 |
| 连通块计数 | ✅ | ✅ 一样好 |

> **内存那一行值得注意**：$10^3 \times 10^3$ 的网格上，
> BFS 最宽的一层可能有上千个点，而 DFS 的最深路径可能有 $10^6$ 层。
> 在 Python 里，**队列宽一点无所谓，栈深一点就要命**——这又是一条选 BFS 的理由。

---

## 61.2　队列必须是 `deque`

**这是 Python BFS 唯一的性能红线。**

```python
# ❌ 每次 pop(0) 都要把后面所有元素前移一格，是 O(n)
q = [s]
u = q.pop(0)

# ✅ deque 是块状双向链表，两端操作都是 O(1)
from collections import deque
q = deque([s])
u = q.popleft()
```

| 队列 $n$ | `list.pop(0)` 总代价 | `deque.popleft()` 总代价 |
| --- | --- | --- |
| $10^3$ | $10^6$，还行 | $10^3$ |
| $10^5$ | $10^{10}$，**必然 TLE** | $10^5$ |
| $10^6$ | $10^{12}$，**跑到天荒地老** | $10^6$ |

### 变体：用 `list` 当队列 + 头指针

大规模下 `deque` 的方法调用开销也会显现。可以改用 `list` + 整数头指针：

```python
def bfs_fast(s, start, adj, n):
    """list + 头指针的 BFS。省掉 deque 的方法调用，快约 1.3-1.6 倍。"""
    dist = [-1] * n
    dist[s] = 0
    q = [s]
    head = 0
    while head < len(q):
        u = q[head]; head += 1           # 「出队」= 指针后移，不搬数据
        d = dist[u] + 1
        for v in adj[u]:
            if dist[v] < 0:
                dist[v] = d
                q.append(v)
    return dist
```

> **为什么这样是对的**：BFS 每个点只入队一次，所以 `q` 最终长度 $\le n$，
> 不会无限增长，「不回收已出队的空间」是可以接受的。
> **但 0-1 BFS 不能这么写**（要从队首插入），必须用 `deque`。

| 写法 | 相对速度 | 适用 |
| --- | --- | --- |
| `list.pop(0)` | ❌ 不可用 | — |
| `deque` | 1× | 通用，**首选** |
| `list` + 头指针 | **1.3–1.6×** | 只需要队尾追加的普通 BFS，$n \ge 10^6$ 时用 |

---

## 61.3　网格 BFS：压一维 + 哨兵边框

网格题（迷宫、洪水、岛屿）占 BFS 题的一大半。有两个**必学的工程技巧**：

**技巧一：二维压成一维。** 用 `idx = i * W + j` 代替 `(i, j)`，
好处是队列里存的是整数而不是元组（省掉元组的创建和解包），`dist` 是一维 `list`。

**技巧二：四周加一圈墙做哨兵。** 这样就**不需要写 4 次边界判断**，
越界的位置自动是墙，被 `grid[v] != WALL` 挡掉。

```python
import sys
from collections import deque


def grid_bfs(rows, n, m, sx, sy, WALL=ord('*')):
    """网格四连通 BFS 模板。rows 是 n 个 bytes（每行一个），坐标 1-based。

    压一维 + 四周哨兵：内层循环只有一次查表，没有 4 次边界比较。
    """
    W = m + 2                                # 加了左右各一列哨兵
    grid = bytearray(b'*' * W)               # 顶部哨兵行
    for r in rows:
        grid += b'*' + r + b'*'
    grid += b'*' * W                         # 底部哨兵行

    dist = [-1] * len(grid)
    s = sx * W + sy                          # 1-based 坐标加了哨兵后正好对上
    dist[s] = 0
    q = deque([s])
    while q:
        u = q.popleft()
        d = dist[u] + 1
        for v in (u - W, u + W, u - 1, u + 1):   # 上下左右
            if dist[v] < 0 and grid[v] != WALL:
                dist[v] = d
                q.append(v)
    return grid, dist, W
```

> **1-based 坐标 + 哨兵边框是绝配**：输入给的坐标是 $1 \sim n$，
> 加了一圈哨兵之后第 1 行数据正好落在下标 1 上，**不需要 $-1$ 再 $+1$**。

**用 `bytearray` 而不是 list of str**：

| 表示 | 单格内存 | 比较代价 | 可修改 |
| --- | --- | --- | --- |
| `list[list[str]]` | 8 字节指针 + 字符串对象 | 字符串比较 | ✅ |
| `list[bytes]`（原始输入） | 紧凑 | **int 比较** | ❌ 不可变 |
| **`bytearray`（压一维）** | **1 字节** | **int 比较** | ✅ **可原地改** |

`bytearray` 还能顺手当 `vis` 用：**直接把访问过的格子改写成墙**，省一个数组。

---

## 61.4　多源 BFS

> **问题形态**：有一组「源点」，求每个点**到最近源点**的距离。

朴素做法是对每个源点跑一次 BFS，$O(k(n+m))$，源点多了就爆。
**正确做法：把所有源点同时塞进初始队列，距离都设为 0，然后跑一次普通 BFS。**

```python
from collections import deque


def multi_source_bfs(sources, adj, n):
    """多源 BFS：dist[v] = v 到最近源点的距离。O(n + m)，和单源一样快。"""
    dist = [-1] * n
    q = deque()
    for s in sources:
        dist[s] = 0
        q.append(s)                      # ★ 全部先入队，再开始扩展
    while q:
        u = q.popleft()
        d = dist[u] + 1
        for v in adj[u]:
            if dist[v] < 0:
                dist[v] = d
                q.append(v)
    return dist
```

**为什么是对的？** 等价于建一个「超级源点 $S$」，向所有源点连一条**边权 0** 的边，
然后从 $S$ 跑 BFS。队列里初始的那批点距离都是 0，单调性依然成立。

**典型题型**：

| 题目描述 | 源点是谁 |
| --- | --- |
| 「每个格子到最近的水的距离」 | 所有水格 |
| 「腐烂的橘子几分钟传染完」 | 所有初始腐烂的橘子 |
| 「树上每个点到最近叶子的距离」 | 所有叶子（**BISHI101**） |
| 「离最近的敌人多远」 | 所有敌人 |
| 「多个起点，问最早何时到终点」 | 所有起点 |

> **识别信号**：题面里出现「**到最近的 XXX 的距离**」，
> 而 XXX 有很多个 —— 立刻想多源 BFS，不要写 $k$ 次单源。

---

## 61.5　0-1 BFS：边权只有 0 和 1

> **问题形态**：边权只有 0 和 1（比如「转弯要花 1，直走免费」「打破一堵墙花 1」）。

用 Dijkstra 当然对，但堆是 $O(m \log n)$ 的，而且 Python 的 `heapq` 常数不小。
**0-1 BFS 用双端队列把它降到 $O(n + m)$**：

> **权 0 的边 → `appendleft`（插队首）；权 1 的边 → `append`（排队尾）。**

```python
from collections import deque


def bfs01(s, adj, n):
    """0-1 BFS：边权只有 0/1 的最短路。O(n + m)。

    adj[u] 是 [(v, w), ...]，w in {0, 1}。
    正确性：队列中的距离值最多只有两种（d 和 d+1），且单调不减，
    所以 0 权边插队首、1 权边接队尾之后，单调性依然成立。
    """
    INF = float("inf")
    dist = [INF] * n
    dist[s] = 0
    q = deque([s])
    while q:
        u = q.popleft()
        du = dist[u]
        for v, w in adj[u]:
            nd = du + w
            if nd < dist[v]:
                dist[v] = nd
                if w:
                    q.append(v)          # 权 1：排队尾
                else:
                    q.appendleft(v)      # 权 0：插队首
    return dist
```

> ⚠️ **0-1 BFS 和普通 BFS 有一个关键区别**：
> **一个点可能被多次入队**（第二次以更小的距离进来），
> 所以判定条件是 `nd < dist[v]` 而**不是** `dist[v] < 0`。
> 出队时可以加一句 `if du > dist[u]: continue` 跳过陈旧副本（可选优化）。

| 边权情况 | 该用什么 | 复杂度 |
| --- | --- | --- |
| 全为 1 | **BFS** | $O(n+m)$ |
| 只有 0 和 1 | **0-1 BFS（双端队列）** | $O(n+m)$ |
| 小整数 $0..k$ | 桶队列 / 分层图 | $O(n+m)$ 或 $O(k(n+m))$ |
| 任意非负 | **Dijkstra + 堆** | $O(m\log n)$ |
| 有负权 | Bellman-Ford / SPFA | $O(nm)$ |

见 [91-最短路](../part8-图与树/91-最短路.md)。

---

## 61.6　双向 BFS

> **问题形态**：起点和终点都已知，状态空间巨大，但答案的步数不大。

从两端同时 BFS，在中间相遇。设答案是 $d$，分支因子是 $b$：

| | 访问的状态数 |
| --- | --- |
| 单向 BFS | $O(b^d)$ |
| **双向 BFS** | $O(2 b^{d/2})$ |

$b = 10, d = 8$ 时，$10^8$ 变成 $2 \times 10^4$——**这是指数级的改善**。

```python
def bidirectional_bfs(start, goal, neighbors):
    """双向 BFS，返回最少步数；不可达返回 -1。

    neighbors(state) 返回该状态的所有后继（要求转移是对称的，即无向图）。
    关键优化：每轮总是扩展**较小的那一侧**，让两棵搜索树保持平衡。
    """
    if start == goal:
        return 0
    fa = {start: 0}                      # 正向已访问：状态 -> 步数
    fb = {goal: 0}                       # 反向已访问
    qa = [start]
    qb = [goal]
    step = 0
    while qa and qb:
        if len(qa) > len(qb):            # ★ 永远扩展较小的一侧
            qa, qb = qb, qa
            fa, fb = fb, fa
        step += 1
        nq = []
        for u in qa:
            for v in neighbors(u):
                if v in fa:
                    continue
                if v in fb:              # 相遇！
                    return fa[u] + 1 + fb[v]
                fa[v] = fa[u] + 1
                nq.append(v)
        qa = nq
    return -1
```

> **双向 BFS 的三个前提，缺一不可**：
> 1. **终点状态必须明确知道**（不能是「满足某条件的任意状态」）；
> 2. **转移必须可逆**（无向图，或反向图容易构造）；
> 3. **答案步数不能太大**，否则两边都会先爆掉。
>
> 实战中双向 BFS 出现频率不高，但**八数码、单词接龙、魔方**这类
> 「状态空间指数级、答案步数十几步」的题几乎必须用它。

---

## 61.7　状态编码与去重

BFS 不只能在图和网格上跑，**任何「状态 + 转移」的问题都能 BFS**。
关键是把状态编成一个**可哈希、最好是整数**的东西。

| 状态 | 编码方式 | 容器 |
| --- | --- | --- |
| 网格坐标 $(i,j)$ | `i * W + j` | `list`（下标即状态） |
| 坐标 + 已用道具数 $k$ | `(i * W + j) * (K+1) + k` | `list` |
| $n$ 个开关的开/关 | 二进制 mask（[46-位运算](../part4-基础算法/46-位运算.md)） | `list`，长 $2^n$ |
| 一个排列（八数码） | 排列的字典序名次（康托展开），或直接用 `str`/`tuple` | `dict` / `list` |
| 多个小整数 | 混合进制打包：`((a * B + b) * C + c)` | `list` |
| 状态空间稀疏/未知 | `tuple` 或 `str` | **`dict` / `set`** |

```python
# 分层图：坐标 (i, j) + 「还剩 k 次穿墙机会」
def encode(i, j, k, W, K):
    return (i * W + j) * (K + 1) + k

def decode(code, W, K):
    code, k = divmod(code, K + 1)
    i, j = divmod(code, W)
    return i, j, k
```

**选 `list` 还是 `dict`？**

| 判据 | 选择 |
| --- | --- |
| 状态数 $\le 10^7$ 且能编成连续整数 | **`list`**（快 2–3 倍，省掉哈希） |
| 状态数未知 / 极度稀疏 | `dict` 或 `set` |
| 状态是 `tuple` 且个数 $\le 10^6$ | `dict` 可以接受 |
| 状态是长字符串 | 先映射成整数编号 |

> **常见错误**：状态没编全就去重。比如「坐标 + 剩余燃料」的题，
> 只用坐标去重会漏掉「同一个格子但燃料不同」的合法状态，答案直接错。
> **去重的维度必须和状态的维度完全一致。**

---

## 61.8　例题

### BISHI105 【模板】单源最短路Ⅰ ‖ 无权图：BFS（中等）

> $n, m \le 2\times10^5$ 的**有向无权图**（可能不连通、可能有重边），
> 输出从 $s$ 到所有点的最短路径长度，不可达输出 $-1$。
> 题面见 [BISHI105 原题（牛客）](https://www.nowcoder.com/practice/359e14832ce1476fadc70dd4bc36b991)。
> 题解见 [`solutions/BISHI105.py`](https://github.com/w3903771/algorithm/blob/main/solutions/BISHI105.py)（已用官方样例验证）。

**无权图的最短路就是 BFS，不要上 Dijkstra**——后者白白多一个 $\log$，
还要多背一个堆。

$n, m$ 到 $2\times10^5$，邻接表**必须用 CSR（压缩稀疏行）**而不是
`[[] for _ in range(n)]` 或 `defaultdict(list)`：

| 邻接表实现 | $2\times10^5$ 点的开销 |
| --- | --- |
| `defaultdict(list)` | 每次 `adj[u]` 都要哈希 + 可能建新 list |
| `[[] for _ in range(n+1)]` | $2\times10^5$ 个 list 对象，光对象头就 ~11 MB |
| **CSR（度数前缀和 + 一个扁平数组）** | **两个 `list`，零对象开销** |

```python
import sys
from collections import deque


def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); m = int(data[1]); s = int(data[2])

    # ---- CSR 邻接表（有向）：先数度数，再前缀和定位，最后填边 ----
    deg = [0] * (n + 2)
    for i in range(3, 3 + 2 * m, 2):
        deg[int(data[i])] += 1
    start = [0] * (n + 2)
    acc = 0
    for i in range(1, n + 1):
        start[i] = acc
        acc += deg[i]
    start[n + 1] = acc
    pos = start[:]                      # 每个点当前的写入位置
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
```

复杂度 $O(n + m)$。时限「其他语言 10 秒」，非常宽裕。

**三个坑**：

1. **图是有向的**，建表时只加 $u \to v$，别顺手加反向；
2. **可能有重边**（样例 1 里 `4 3` 出现了两次），BFS 对重边天然免疫
   （第二次看到时 `dist` 已经填过了），不需要去重；
3. `start[n+1] = acc` 这一行不能漏——最后一个点的邻居区间靠它定右端。

> **CSR 的构造是三步**：数度数 → 前缀和求每个点的起始下标 → 逐边填入。
> 这个套路在所有大规模图论题里都要用，见
> [90-图的表示与遍历](../part8-图与树/90-图的表示与遍历.md)。

### BISHI80 走迷宫（简单）

> $n, m \le 1000$ 的网格，`.` 可走、`*` 是障碍，四连通。
> 求 $(x_s,y_s)$ 到 $(x_t,y_t)$ 的最少步数，不可达输出 $-1$。
> 题面见 [BISHI80 原题（牛客）](https://www.nowcoder.com/practice/e88b41dc6e764b2893bc4221777ffe64)。
> 题解见 [`solutions/BISHI80.py`](https://github.com/w3903771/algorithm/blob/main/solutions/BISHI80.py)（已用官方样例验证）。

网格 BFS 的标准模板题，61.3 的技巧全部用上。

```python
import sys
from collections import deque


def main():
    data = sys.stdin.buffer.read().split()
    n, m = int(data[0]), int(data[1])
    xs, ys, xt, yt = int(data[2]), int(data[3]), int(data[4]), int(data[5])
    rows = data[6:6 + n]

    W = m + 2
    BLOCK = ord('*')
    # 压成一维并加一圈 '*' 哨兵，越界判断被墙自动挡掉
    grid = bytearray(b'*' * W)
    for r in rows:
        grid += b'*' + r + b'*'
    grid += b'*' * W

    s = xs * W + ys                      # 1-based 坐标 + 哨兵，正好对上
    t = xt * W + yt
    dist = [-1] * len(grid)
    if grid[t] == BLOCK:                 # 终点本身是障碍
        sys.stdout.write("-1\n")
        return

    dist[s] = 0
    q = deque([s])
    while q:
        u = q.popleft()
        if u == t:
            break                        # 提前退出，省一半时间
        d = dist[u] + 1
        for v in (u - W, u + W, u - 1, u + 1):
            if dist[v] < 0 and grid[v] != BLOCK:
                dist[v] = d
                q.append(v)
    sys.stdout.write("%d\n" % dist[t])


main()
```

复杂度 $O(nm) = 10^6$。时限「其他语言 6 秒」，够用。

**四个坑**：

1. **起点保证可通行，但终点不保证**（样例 2、3 就是走不到）。
   要么像上面那样先判 `grid[t] == BLOCK`，要么靠 `dist[t]` 初值 $-1$ 兜底；
2. **起点 == 终点时答案是 0**，靠 `dist[s] = 0` 天然正确；
3. `dist` 用 `list of int` 而不是 `bytearray`——步数最大可达 $10^6$，
   一个字节存不下；
4. 「找到终点就 `break`」在最坏情况下没用（终点在最远处），
   但在多数数据上能省掉一半的扩展。

> **$10^6$ 个格子在 Python 里的现实性**：主循环 $10^6$ 次出队 + $4\times10^6$ 次
> 邻居检查，约 $5\times10^6$ 次 Python 层操作，估计 2–4 秒。
> 时限 6 秒能过，但**不能再套任何额外常数**（比如用元组存坐标、
> 每次算 `divmod`）——这正是要压一维、加哨兵的原因。

### BISHI81 剪纸游戏（简单）

> $n, m \le 1000$ 的纸张，`.` 是被剪去的格子、`*` 是保留的。
> 每个 `.` 的四连通块是一个被剪下的图案，问其中有多少个是**实心长方形**。
> 题面见 [BISHI81 原题（牛客）](https://www.nowcoder.com/practice/33054daa2cc04fd6b97a0d18ccfc66a0)。
> 题解见 [`solutions/BISHI81.py`](https://github.com/w3903771/algorithm/blob/main/solutions/BISHI81.py)（已用官方样例验证）。

连通块搜索 + 一个非常干净的判定技巧：

> **一个连通块是实心长方形 $\iff$ 它的格子数 $=$ 它的外接矩形面积。**

因为外接矩形面积一定 $\ge$ 块的大小，取等号说明外接矩形被完全填满、没有缺口，
**同时自动排除了 L 形、空心、十字形**这些情况。所以只要在 BFS 过程中
顺手维护 `minr/maxr/minc/maxc` 和 `size`，**不需要真的逐格验证矩形内部**。

```python
import sys
from collections import deque


def main():
    data = sys.stdin.buffer.read().split()
    n, m = int(data[0]), int(data[1])
    rows = data[2:2 + n]

    W = m + 2
    CUT = ord('.')
    grid = bytearray(b'*' * W)
    for r in rows:
        grid += b'*' + r + b'*'
    grid += b'*' * W

    ans = 0
    q = deque()
    for start in range(W, len(grid) - W):
        if grid[start] != CUT:
            continue
        grid[start] = ord('*')            # ★ 入队即标记：直接把 '.' 改写成 '*'
        q.append(start)
        r0, c0 = divmod(start, W)
        minr = maxr = r0
        minc = maxc = c0
        size = 0
        while q:
            u = q.popleft()
            size += 1
            r, c = divmod(u, W)
            if r < minr: minr = r
            elif r > maxr: maxr = r
            if c < minc: minc = c
            elif c > maxc: maxc = c
            for v in (u - W, u + W, u - 1, u + 1):
                if grid[v] == CUT:
                    grid[v] = ord('*')
                    q.append(v)
        # 块大小 == 外接矩形面积  <=>  实心长方形
        if size == (maxr - minr + 1) * (maxc - minc + 1):
            ans += 1
    sys.stdout.write("%d\n" % ans)


main()
```

复杂度 $O(nm)$。

**三个坑**：

1. **直接把访问过的 `.` 改写成 `*`**，省掉一个 `vis` 数组，
   这在 `bytearray` 上是 $O(1)$ 的原地修改；
2. **`q` 在循环外创建、循环内复用**。如果每个连通块都 `deque()` 新建一个，
   $10^6$ 次对象创建的开销不小；
3. 因为「入队即标记」，块结束时队列一定是空的，
   所以下一个块可以安全复用同一个 `q`。

### BISHI82 没挡住洪水（简单）

> $N \le 1000$ 的方阵，`.` 是水、`#` 是空地，四连通的 `#` 组成一个区域。
> 洪水上涨**一轮**：所有与 `.` 上下左右相邻的 `#` 都会被淹。
> 问有多少个区域会被**完全**淹没。
> 题面见 [BISHI82 原题（牛客）](https://www.nowcoder.com/practice/6d62436fda5f4ef997e68d1ce1dd6eb2)。
> 题解见 [`solutions/BISHI82.py`](https://github.com/w3903771/algorithm/blob/main/solutions/BISHI82.py)（已用官方样例验证）。

**这题一半的分在读题上。** 洪水上涨是**一次性、同时**发生的一轮，
**不是反复扩散到收敛**。所以：

> 一个区域被「完全」淹没 $\iff$ 区域里的**每一个**格子都至少有一个四方向邻居是 `.`。

两个常见错解：

| 错解 | 错在哪 |
| --- | --- |
| 以为洪水一轮轮往里渗 | 那样所有区域都会被淹完，答案恒等于区域总数 |
| 只判「区域边界挨着水」 | 只淹掉了外壳，厚度 $\ge 3$ 的实心块中心淹不到 |

```python
import sys
from collections import deque


def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    rows = data[1:1 + n]

    W = n + 2
    LAND = ord('#')
    WATER = ord('.')
    SEEN = ord('x')                       # ★ 第三种字符：已访问的陆地
    grid = bytearray(b'.' * W)            # 题面保证边界全是水，补 '.' 与题意一致
    for r in rows:
        grid += b'.' + r + b'.'
    grid += b'.' * W

    ans = 0
    q = deque()
    for start in range(W, len(grid) - W):
        if grid[start] != LAND:
            continue
        grid[start] = SEEN
        q.append(start)
        all_flooded = True
        while q:
            u = q.popleft()
            touched = False               # 本格是否挨着水
            for v in (u - W, u + W, u - 1, u + 1):
                c = grid[v]
                if c == WATER:
                    touched = True
                elif c == LAND:
                    grid[v] = SEEN
                    q.append(v)
            if not touched:
                all_flooded = False       # 有一格淹不到，整块就不算完全消失
        if all_flooded:
            ans += 1
    sys.stdout.write("%d\n" % ans)


main()
```

**核心坑（也是这题最容易 WA 的一点）**：
**已访问标记不能写成 `.`**。判定「该格是否会被淹」要用**原始**地图上的水，
如果把访问过的陆地改写成 `.`，同区域的兄弟格就会被误判成水，答案偏大。
所以必须引入**第三种字符** `'x'` 来区分「水」和「已访问的陆地」。

> **这是「原地改写 grid 当 vis」这个技巧的边界**：
> 只有当「已访问」和「障碍」在后续逻辑里**完全等价**时才能合并成一个值。
> BISHI81 里可以（后面不再关心 `*` 是原本的还是改写的），
> BISHI82 里不行。**写之前先问一句：我后面还需要区分它们吗？**

### BISHI83 迷宫问题（中等）

> $h, w \le 100$ 的 01 迷宫，输出一条从 $(0,0)$ 到 $(h-1,w-1)$ 的可行路径，
> 每行输出 `(x,y)`。保证路径存在且唯一。
> 题面见 [BISHI83 原题（牛客）](https://www.nowcoder.com/practice/cf24906056f4488c9ddb132f317e03bc)。
> 题解见 [`solutions/BISHI83.py`](https://github.com/w3903771/algorithm/blob/main/solutions/BISHI83.py)（已用官方样例验证）。

BFS 求最短路 + **前驱数组回溯路径**。
题目保证可行路径唯一，所以「最短路」和「那条唯一路径」是同一条。
（[60 章](60-DFS深度优先搜索.md#bishi83-迷宫问题中等) 给了 DFS 显式栈的对照版本。）

```python
import sys
from collections import deque


def main():
    data = sys.stdin.buffer.read().split()
    h, w = int(data[0]), int(data[1])
    g = data[2:2 + h * w]                 # b'0' / b'1'，空格分隔的 token

    WALL = b'1'
    n = h * w
    pre = [-2] * n                        # -2 未访问，-1 起点，其余为前驱下标
    start, goal = 0, n - 1
    pre[start] = -1
    q = deque([start])
    while q:
        u = q.popleft()
        if u == goal:
            break
        x, y = divmod(u, w)
        if x > 0:
            v = u - w
            if pre[v] == -2 and g[v] != WALL:
                pre[v] = u; q.append(v)
        if x + 1 < h:
            v = u + w
            if pre[v] == -2 and g[v] != WALL:
                pre[v] = u; q.append(v)
        if y > 0:
            v = u - 1
            if pre[v] == -2 and g[v] != WALL:
                pre[v] = u; q.append(v)
        if y + 1 < w:
            v = u + 1
            if pre[v] == -2 and g[v] != WALL:
                pre[v] = u; q.append(v)

    path = []
    u = goal
    while u != -1:                        # 从终点顺着 pre 倒推回起点
        x, y = divmod(u, w)
        path.append("(%d,%d)" % (x, y))
        u = pre[u]
    path.reverse()
    sys.stdout.write("\n".join(path) + "\n")


main()
```

**两个坑**：

1. **输入是 $h \times w$ 个空格分隔的 0/1 整数**（不是一整行字符串！），
   所以这里没法用「一行一个 bytes」的读法，`split()` 之后每个格子是一个 token。
   **读入格式一定要看样例，不同题的网格给法不一样**；
2. **输出格式以样例为准**：文字描述写的是「两个整数」，样例给的是 `(x,y)`。

> **BFS 输出路径的通用套路**：
> 1. `pre[v] = u`，在**第一次访问 $v$ 时**记录；
> 2. 从终点倒推：`while u != start: path.append(u); u = pre[u]`；
> 3. `path.reverse()`。
>
> 不要试图在 BFS 过程中存「到每个点的完整路径」——那是 $O(n^2)$ 的内存。

### BISHI84 时津风的资源收集（中等）

> 4 种资源初始都是 10，每次操作只能对**单一**资源做：$\pm1$、$\pm10$、$\pm100$、
> 直接设为 300、直接设为 10。资源必须始终在 $[10, 300]$ 内。
> $T \le 10^5$ 组询问，每组给目标 $(a,b,c,d)$，求最少操作次数。
> 题面见 [BISHI84 原题（牛客）](https://www.nowcoder.com/practice/5a6f83a0e0214ba5a77f6cdc71a3027b)。
> 题解见 [`solutions/BISHI84.py`](https://github.com/w3903771/algorithm/blob/main/solutions/BISHI84.py)（已用官方样例验证）。

**这题是「状态空间拆分」的教科书例子**，也是本章最值得想清楚的一道。

如果老老实实把 $(a,b,c,d)$ 当四维状态，状态数是 $291^4 \approx 7.2\times10^9$，
**内存和时间都是天文数字**。但注意：

> 每次操作只作用于**单一**资源，而合法性约束也只是「每种资源各自落在 $[10,300]$」——
> **四种资源之间毫无耦合**。

所以总操作数 $=$ 各资源独立所需操作数之和，只要求出**一张一维表**
$f[v] = $「单个资源从 10 变到 $v$ 的最少步数」即可。$f$ 就是 291 个点上的
无权最短路，**一次 BFS 搞定**。

```python
import sys
from collections import deque

LO, HI = 10, 300


def build_table():
    """f[v] = 单个资源从 10 出发变到 v 的最少操作次数。"""
    f = [-1] * (HI + 1)
    f[LO] = 0
    q = deque([LO])
    while q:
        v = q.popleft()
        d = f[v] + 1
        # 出边：±1、±10、±100，以及两条「任意位置一步可达」的传送边
        for u in (v - 1, v + 1, v - 10, v + 10, v - 100, v + 100, HI, LO):
            if LO <= u <= HI and f[u] < 0:
                f[u] = d
                q.append(u)
    return f


def main():
    f = build_table()
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    out = []
    idx = 1
    for _ in range(t):
        a = int(data[idx]); b = int(data[idx + 1])
        c = int(data[idx + 2]); d = int(data[idx + 3])
        idx += 4
        out.append(str(f[a] + f[b] + f[c] + f[d]))   # 四维独立，直接求和
    sys.stdout.write("\n".join(out) + "\n")


main()
```

BFS 只有 291 个点、每点 8 条边，是常数级；$T$ 次询问每次 $O(1)$ 查表。

**手动复核样例**（目标 `10 100 200 300`）：
$f[10]=0$；$f[100]=2$（$+100$ 到 110，再 $-10$）；
$f[200]=2$（设为 300，再 $-100$）；$f[300]=1$（设为上限）。
合计 $0+2+2+1=5$ ✓

**三个坑**：

1. **「设为上限/下限」是从任意状态一步可达的边**，
   别写成只有边界点才有——样例里 $10 \to 300$ 只用 1 步正是靠这条边；
2. **必须预处理**。若对每组询问现搜，$10^5 \times$ BFS 必然 TLE；
3. $T$ 可达 $10^5$，**输出必须 `"\n".join` 一次性 `write`**。

> **本题给出的判据**：多维状态的 BFS，先问一句
> **「各维之间是否互相独立？」** 如果转移只动一维、约束也只管一维，
> 那就拆成 $k$ 个一维问题，指数级的状态空间瞬间坍缩成线性。

### BISHI97 旺仔哥哥走迷宫（中等）

> $n, m \le 10^5$ 的无向图，每个点有 0/1 的陷阱标记，只能经过安全点。
> 问 1 号点能否到 $n$ 号点，输出 `Yes` / `No`。
> 题面见 [BISHI97 原题（牛客）](https://www.nowcoder.com/practice/4b4ee516c23d4bd2b838646363b5c395)。
> 题解见 [`solutions/BISHI97.py`](https://github.com/w3903771/algorithm/blob/main/solutions/BISHI97.py)（已用官方样例验证）。

带**点权限制**的连通性判定：把陷阱点当作不存在的点删掉，剩下的图上跑一次 BFS。

```python
import sys
from collections import deque


def main():
    data = sys.stdin.buffer.read().split()
    n, m = int(data[0]), int(data[1])
    trap = data[2:2 + n]                    # b'0' / b'1'
    ONE = b'1'

    if trap[0] == ONE or trap[n - 1] == ONE:   # 起点或终点本身有陷阱
        sys.stdout.write("No\n")
        return

    adj = [[] for _ in range(n + 1)]
    p = 2 + n
    for _ in range(m):
        a = int(data[p]); b = int(data[p + 1]); p += 2
        if trap[a - 1] == ONE or trap[b - 1] == ONE:
            continue                        # ★ 建表时就把陷阱点的边扔掉
        adj[a].append(b)
        adj[b].append(a)

    vis = bytearray(n + 1)
    vis[1] = 1
    q = deque([1])
    while q:
        u = q.popleft()
        if u == n:
            sys.stdout.write("Yes\n")
            return
        for v in adj[u]:
            if not vis[v]:
                vis[v] = 1
                q.append(v)
    sys.stdout.write("No\n")


main()


```

**三个坑**：

1. **起点 1 自己可能就有陷阱**，此时直接 `No`（BFS 都不该开始）；终点 $n$ 同理；
2. **$n = 1$ 时起点即终点**，只要 1 号房安全就是 `Yes`——
   上面代码在第一轮 `u == n` 就命中返回，天然正确；
3. **在建表时过滤陷阱点**（而不是在 BFS 内层判 `trap[v]`），
   把判断从 $O(m)$ 次内层循环挪到 $O(m)$ 次建表，常数更小、代码更干净。

> **为什么这题不用递归 DFS**：$n = 10^5$，这张图可能是一条长链，
> 递归深度 $10^5$ 必然 `RecursionError` 甚至静默崩溃。
> **BFS 天然迭代，这是它在 Python 里最大的优势。**

### BISHI101 世界树上找米库（中等）

> $T \le 10^4$ 组，每组一棵 $n$ 个点的无根树（$\sum n \le 2\times10^5$）。
> 度数为 1 的点叫 Sekai 点。Miku 点 = 在**非** Sekai 点中，
> 「到最近的 Sekai 点的距离」最大的那些点。输出个数和升序编号。
> 题面见 [BISHI101 原题（牛客）](https://www.nowcoder.com/practice/9dd512f784b24ece85c81600aa3bc06c)。
> 题解见 [`solutions/BISHI101.py`](https://github.com/w3903771/algorithm/blob/main/solutions/BISHI101.py)（已用官方样例验证）。

**多源 BFS 的模板题**。逐点单源 BFS 是 $O(n^2)$，必挂；
把**所有叶子同时塞进队列**（距离 0）跑一次 BFS，
出队顺序保证每个点第一次被访问时拿到的就是「到最近叶子的距离」。

```python
import sys
from collections import deque


def main():
    data = sys.stdin.buffer.read().split()
    ptr = 0
    T = int(data[ptr]); ptr += 1
    out = []
    for _ in range(T):
        n = int(data[ptr]); ptr += 1
        us = [0] * (n - 1)
        vs = [0] * (n - 1)
        deg = [0] * (n + 2)
        for i in range(n - 1):
            a = int(data[ptr]); b = int(data[ptr + 1]); ptr += 2
            us[i] = a; vs[i] = b
            deg[a] += 1
            deg[b] += 1

        # ---- CSR 邻接表 ----
        start = [0] * (n + 2)
        s = 0
        for i in range(1, n + 1):
            start[i] = s
            s += deg[i]
        start[n + 1] = s
        pos = start[:]
        adj = [0] * s
        for i in range(n - 1):
            a = us[i]; b = vs[i]
            adj[pos[a]] = b; pos[a] += 1
            adj[pos[b]] = a; pos[b] += 1

        # ---- 多源 BFS：所有叶子（Sekai 点）同时入队，距离 0 ----
        dist = [-1] * (n + 1)
        q = deque()
        for u in range(1, n + 1):
            if deg[u] == 1:
                dist[u] = 0
                q.append(u)
        while q:
            u = q.popleft()
            d = dist[u] + 1
            for i in range(start[u], start[u + 1]):
                v = adj[i]
                if dist[v] < 0:
                    dist[v] = d
                    q.append(v)

        best = -1
        for u in range(1, n + 1):
            if deg[u] != 1 and dist[u] > best:   # ★ 只在非叶子里评选
                best = dist[u]
        res = [u for u in range(1, n + 1) if deg[u] != 1 and dist[u] == best]
        out.append(str(len(res)))
        out.append(" ".join(map(str, res)))
    sys.stdout.write("\n".join(out) + "\n")


main()
```

复杂度 $O(\sum n)$。

**手动复核样例 2**：叶子 $=\{1,6,8,9,10\}$，多源 BFS 得
$dist[2]=dist[3]=dist[5]=dist[7]=1$，$dist[4]=2$（邻居 3、5 都是 1）。
非叶子中最大是 4 号点的 2，输出 `1` / `4` ✓

**四个坑**：

1. **叶子自身 `dist = 0`，但它们不参与最大值的评选**（Miku 点不能是 Sekai 点），
   统计时要跳过 `deg == 1` 的点。这是本题最容易漏的一句；
2. $n \ge 3$ 保证了树上一定存在非叶子点，不会出现「答案集合为空」；
3. **多组数据不要反复 new 出 $2\times10^5$ 个小 `list`**，CSR 只分配两个扁平数组；
4. $T$ 可达 $10^4$，所有输出攒进一个 list 最后一次 `join`。

> **这题的多源 BFS 还有一个等价说法**：它就是在求树上每个点的
> 「**到最近叶子的距离**」，也叫树的「内部深度」。
> 取到最大值的点集合与树的**重心 / 中心**有关，见
> [94-树上算法](../part8-图与树/94-树上算法.md)。

---

## 61.9　本章速查

| 要点 | 结论 |
| --- | --- |
| 核心性质 | **边权全为 1 时，第一次访问即最短** |
| 容器 | **必须 `collections.deque`** |
| `list.pop(0)` | $O(n)$，$10^5$ 起就是 TLE |
| 标记时机 | **入队即标记**，不是出队才标记 |
| `dist = [-1]*n` | 一身三职：未访问标记 + 距离 + 不可达输出值 |
| 递归风险 | **零**——BFS 天然迭代，是 Python 的首选 |
| 网格题 | **压一维 + 四周哨兵 + `bytearray`** |
| 网格 vis | 可以直接原地把格子改写成墙（除非后面要区分） |
| 大图邻接表 | **CSR**（度数前缀和 + 扁平数组），不要 `defaultdict(list)` |
| $n \ge 10^6$ 的普通 BFS | `list` + 头指针，比 `deque` 快 1.3–1.6× |
| 多源 BFS | **所有源点距离 0 一起入队**，其余不变 |
| 0-1 BFS | 权 0 → `appendleft`，权 1 → `append`；判定用 `nd < dist[v]` |
| 双向 BFS | $O(b^d) \to O(2b^{d/2})$；每轮扩展较小的一侧 |
| 状态编码 | 混合进制打包成整数；能用 `list` 就别用 `dict` |
| 去重维度 | **必须和状态维度完全一致** |
| 输出路径 | `pre[]` 前驱数组 + 倒推 + `reverse` |
| 多维状态 | 先问「各维是否独立」，独立就拆成 $k$ 个一维（BISHI84） |

| 看到什么 → 想到 BFS |
| --- |
| 「最少步数 / 最少操作次数 / 最短路径」且边权都是 1 |
| 「到最近的 XXX 的距离」→ **多源 BFS** |
| 「几分钟后全部扩散完」→ 多源 BFS，答案是最大 dist |
| 「洪水 / 传染 / 感染」类模拟 |
| 图很大又要 DFS 的场合（怕爆栈）→ 改用 BFS |
| 边权只有 0/1 → **0-1 BFS**，别上 Dijkstra |
| 状态空间指数级但答案步数小 → **双向 BFS** |

| 看到什么 → **不要**用 BFS |
| --- |
| 边权是任意正数 → **Dijkstra**（[91 章](../part8-图与树/91-最短路.md)） |
| 要枚举所有方案 → **DFS 回溯**（[60 章](60-DFS深度优先搜索.md)） |
| 树上后序 DP → DFS 两趟法 |

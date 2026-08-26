---
id: graph/basic
title: 图的表示与遍历
volume: 1
lang: py
---

# 第 90 章　图的表示与遍历

<!-- CHAPTER-EXAMPLES -->
> **前置**：[链表](../ds/linked-list.md)、[队列与双端队列](../ds/queue.md)、[DFS深度优先搜索](../search/dfs.md)、[BFS广度优先搜索](../search/bfs.md)

图论题的第一步永远是**建图**。这一步在 C++ 里是无脑的，在 Python 里却是
**能决定 AC 还是 TLE 的一步**——同样一张 $2\times10^5$ 个点的图，
`defaultdict(list)` 和 CSR 之间可以差出好几倍。

这一章把「怎么存图」和「怎么遍历图」讲透，后面四章全部建立在它上面。

---

## 1　基本概念

先把定义列成术语表：

> 图由点集和边集构成，记为 $G = (V, E)$，$V$ 是点集，$E$ 是边集。
> 通常令 $n = |V|$，$m = |E|$。
>
> 无向边用 $u - v$ 表示，有向边用 $u \to v$ 表示。**无向边可以用两条方向相反的有向边表示**。
>
> 边可能带有权值，用来表示长度或者其他的意义。
>
> 无向图中与一个节点相连的边的数量称为**度数**。有向图中进入一个点的边数为**入度**，
> 从一个点出发的边数为**出度**。
>
> 如果边的两个端点相同，则称为**自环**。某两个节点之间可能有多条边相连，
> 这些边都称为**重边**。没有重边和自环的图是**简单图**。
>
> **路径**是一个序列 $[x_1, x_2, \dots, x_k]$，其中相邻两个节点之间有边相连。
> 如果 $x_1 = x_k$，则称为**环**。如果路径中没有重复元素，则称为**简单路径**。
>
> 在无向图中，如果两个节点之间有路径相连则这两个节点是**连通**的。
> **连通块**是一个极大的点集，其中任意两个节点之间都是连通的。
> 如果所有节点之间都是连通的，那么 $G$ 是**连通图**。

再补三条后面天天用的：

| 概念 | 定义 | 关键性质 |
| --- | --- | --- |
| **树** | $n$ 个点、$n-1$ 条边的连通图 | 任意两点间**有且仅有**一条简单路径 |
| **DAG（拓扑图）** | 没有环的有向图 | 存在拓扑序（[拓扑排序](topo.md)） |
| **二分图** | 点集可分成两个独立集 | 等价于**不含奇环**（[二分图](match/bipartite.md)） |

> **握手定理**：无向图中 $\sum_{v} \deg(v) = 2m$。
> 这条在「判断输入是否合法」「估算邻接表总长度」时反复要用：
> **CSR 的扁平数组长度就是 $2m$**（无向）或 $m$（有向）。

**读题时必须立刻确认的五件事**，写错任何一条整题作废：

| 要确认的 | 影响 |
| --- | --- |
| 有向还是无向 | 建表时加一条边还是两条 |
| 是否有重边 | 影响去重、影响 CSR 数组长度估算 |
| 是否有自环 | 度数统计、二分图判定（自环必非二分图） |
| 是否保证连通 | 决定要不要**对每个未访问点都起一轮**遍历 |
| 点编号从 0 还是 1 开始 | 数组开 `n` 还是 `n+1` |

> ⚠️ 「保证连通」这四个字**不可轻信**。BISHI100 的题面白纸黑字写着
> 「保证连通」，但它的第二组官方样例就是不连通的（三角形 $1$-$2$-$3$ 加一条 $4$-$5$）。
> **永远写成「对每个未访问点都起一轮」的形式**，多写两行，换来不被坑。

---

## 2　四种存图方式

### 方式一：邻接矩阵

> 邻接矩阵是一个 $n \times n$ 的矩阵 $M$，如果 $u$ 和 $v$ 之间有有向边 $u \to v$，
> 则 $M[u][v] = 1$。如果是无向边，则 $M[u][v] = M[v][u] = 1$。
> 如果有非零边权，可以设 $M[u][v]$ 为边权。
>
> 邻接矩阵的缺点：**稀疏图中查找边的效率不高，处理重边麻烦，空间复杂度 $\Theta(n^2)$**。

```python
# [片段] 邻接矩阵：只在 n 很小（<= 500，Floyd 场景）时用
INF = float("inf")
g = [[INF] * (n + 1) for _ in range(n + 1)]  # 开到 n+1 行列，点号 1..n 直接当下标
for i in range(n + 1):
    g[i][i] = 0                              # 自己到自己是 0，不能留 INF
for _ in range(m):
    u, v, w = ...
    if w < g[u][v]:                          # ★ 重边取最小，别直接覆盖
        g[u][v] = g[v][u] = w                # 两个方向都填 -> 无向图；有向只填前者
```

> **重边的坑**：邻接矩阵天然只能存一条边，所以遇到重边**必须取 min**
> （最短路场景）或取 max（最大生成树场景）。写成 `g[u][v] = w` 会被后来的
> 大边权覆盖掉先前的小边权。这是邻接矩阵最常见的 WA。

Python 下的现实规模：$n \le 500$ 时矩阵有 $2.5\times10^5$ 格，还算轻松；
$n = 1000$ 时 $10^6$ 格，**光初始化就要 1 秒左右**，已经是上限。
$n \le 100$（Floyd 的现实上限）才是它的舒适区，见 [最短路](shortest-path.md)。

### 方式二：list of list（默认选择）

```python
# [片段] 定长 list of list：下标即点号
adj = [[] for _ in range(n + 1)]             # ★ 定长，不是 defaultdict
                                             # 每个点一个独立的空 list，下标 0 空着不用
for _ in range(m):
    u, v = ...
    adj[u].append(v)                         # u 的邻居里记下 v
    adj[v].append(u)                         # 无向图才加这一行；有向图删掉它
```

带权就存元组：`adj[u].append((v, w))`。

**为什么绝对不要用 `defaultdict(list)`**：

| | `defaultdict(list)` | `[[] for _ in range(n+1)]` |
| --- | --- | --- |
| 每次 `adj[u]` | 哈希 `u` + 字典查找 + 可能触发 `__missing__` 建新 list | 一次数组下标 |
| 遍历顺序 | 按插入顺序，**孤立点根本不存在** | 下标 $1..n$ 天然有序 |
| 内存 | 字典 + $n$ 个 list | $n$ 个 list |
| 典型开销 | 慢 1.5–2 倍 | 基准 |

`defaultdict` 唯一有意义的场景是**点编号不连续**（比如点是字符串、
或编号高达 $10^9$）。这时正确做法也不是 `defaultdict`，而是
**先离散化成 $0..n-1$ 再用数组**，见 [桶计数与离散化](../basic/discretization.md)。

### 方式三：链式前向星（C++ 的经典写法）

结构如下：

```text
struct Edge:
    int u, v, w  // 起点、终点、边权
    int nxt      // 链表的下一个元素
Edge e[]         // 边数组
int G[N]         // 链表的第一个元素
```

> 如果采用数组存边，一般下标从 $0$ 开始用。因为对于无向图，
> 每条无向边拆分出来的两条边在数组中相邻，如果其中一条边的下标是 `x` 的话，
> 那么另外一条边的下标就是 `x ^ 1`。
>
> 如果要访问节点 $u$ 的所有边，从 `G[u]` 开始遍历链表即可。

Python 直译版：

```python
# [片段] 链式前向星：head / nxt / to 三数组模拟链表
head = [-1] * (n + 1)                        # head[u] = u 的第一条出边下标，-1 = 没有出边
to = [0] * (2 * m)                           # to[i] = 第 i 条边的终点；无向图开 2m
nxt = [0] * (2 * m)                          # nxt[i] = 同一个起点的下一条边的下标
wt = [0] * (2 * m)                           # wt[i] = 第 i 条边的边权
cnt = 0                                      # 已加入的边数，也是下一条边的下标

def add(u, v, w):
    """把边 u->v 插到 u 的链表头部。O(1)。"""
    global cnt
    to[cnt] = v
    wt[cnt] = w
    nxt[cnt] = head[u]                       # 新边指向原来的第一条
    head[u] = cnt                            # 新边成为第一条
    cnt += 1                                 # 头插法：先加的边反而排在后面

# 遍历 u 的所有出边
i = head[u]
while i != -1:                               # -1 是链表末尾的哨兵
    v = to[i]
    w = wt[i]
    i = nxt[i]                               # 顺着链表往下一条边走
```

> **这就是 BISHI95 的标题所指的数据结构**。理解它是必须的（C++ 题解满屏都是它），
> 但在 **Python 里它比 list of list 更慢**：
> `while i != -1: ... i = nxt[i]` 每轮要做 3 次列表下标 + 1 次比较，
> 而 `for v in adj[u]` 的迭代整个落在 C 层。
> **链式前向星在 Python 下只有教学价值，实战请用 CSR。**

链式前向星还有两个 Python 用不上、但读 C++ 代码时要认识的性质：

| 性质 | 说明 |
| --- | --- |
| **边是倒序的** | 后加的边先被遍历（头插法），所以输出顺序常与输入相反 |
| **`i ^ 1` 是反向边** | 从 0 开始成对加边时成立，网络流的「反向弧」全靠它 |

### 方式四：CSR / 压缩稀疏行（Python 的最优解）

**CSR** 是 Compressed Sparse Row（压缩稀疏行）的缩写，本是稀疏矩阵的存储格式：
用两个扁平数组代替 $n$ 个小 `list`，一个记「每行从哪里开始」，一个把所有元素首尾相接。
搬到图上，「行」就是点，「行里的元素」就是它的邻居。

CSR 是链式前向星的「排好序的紧凑版」：先数出每个点的度数，
前缀和算出每个点在大数组里的起始位置，再扫一遍把邻居填进去。
**全程没有 `append` 扩容，没有小对象，只有两三个大 `list`。**

```python
def build_csr(n, us, vs, directed=False):
    """CSR 邻接表。返回 (start, adj)：u 的邻居是 adj[start[u]:start[u+1]]。

    us / vs 是等长的边端点数组，点编号 1..n。O(n + m)，兼容 Python 3.9。

    三趟建表，是全书反复使用的基础设施：
      ① 数度数：每个点有多少条邻边；
      ② 前缀和：把度数累加成每个点在大数组 adj 里的起始下标；
      ③ 回填：再扫一遍边，用游标把邻居写进各自的格子。
    """
    m = len(us)
    # ---- 第一趟：数度数。deg[x] = x 的邻边条数 ----
    deg = [0] * (n + 2)                      # 长度取 n+2，第二趟要写 start[n+1]
    for x in us:
        deg[x] += 1
    if not directed:                         # 无向边算两次度数：两个端点各一次
        for x in vs:
            deg[x] += 1
    # ---- 第二趟：度数前缀和 -> 每个点的起始下标 ----
    start = [0] * (n + 2)
    acc = 0
    for i in range(1, n + 1):                # 循环里 acc 恒等于「1..i-1 的度数和」
        start[i] = acc                       # 所以它正是 i 的邻居区间左端
        acc += deg[i]
    start[n + 1] = acc                       # 末尾哨兵，同时也是 adj 的总长度
    # ---- 第三趟：回填邻居 ----
    pos = start[:]                           # 游标副本；start 要原样返回，不能被改
    adj = [0] * acc                          # 一次开够，全程没有 append 扩容
    for i in range(m):
        a = us[i]
        adj[pos[a]] = vs[i]                  # 写进 a 的下一个空位
        pos[a] += 1                          # 游标右移一格，下条边填到它后面
        if not directed:
            b = vs[i]
            adj[pos[b]] = a                  # 无向图：反方向再存一份
            pos[b] += 1
    return start, adj
```

带权版只要再开一个等长的 `wt` 数组，填 `adj` 时同步填 `wt`：

```python
# [片段] 带权 CSR 的遍历方式
for i in range(start[u], start[u + 1]):      # u 的邻居恰好占据 [start[u], start[u+1])
    v = adj[i]                               # 邻居点号
    w = wt[i]                                # 与它同一个下标 i，两个数组严格对齐
    ...
```

> **CSR 的两个隐藏优点**：
> 1. `start[u+1] - start[u]` 直接就是 $u$ 的度数，不用另开数组；
> 2. `adj` 是一个大 `list`，内存连续，缓存友好；
>    $3\times10^5$ 个点时它比 `[[] for _ in range(n+1)]` 少了
>    $3\times10^5$ 个 list 对象头（每个 56 字节，合计约 17 MB）。

### 存图方式选型表

| 方式 | 建表 | 查「$u,v$ 之间有没有边」 | 空间 | Python 实测 | 什么时候用 |
| --- | --- | --- | --- | --- | --- |
| 邻接矩阵 | $O(n^2)$ | $O(1)$ | $O(n^2)$ | $n \le 500$ | Floyd、稠密图、需要 $O(1)$ 查边 |
| **list of list** | $O(n+m)$ | $O(\deg u)$ | $O(n+m)$ | 基准 | **$n \le 10^5$ 的默认选择** |
| 链式前向星 | $O(n+m)$ | $O(\deg u)$ | $O(n+m)$ | **慢 1.5–2 倍** | 只在读 C++ 题解时需要认识 |
| **CSR** | $O(n+m)$ | $O(\deg u)$ | $O(n+m)$ | **最快，省内存** | **$n \ge 2\times10^5$ 必用** |
| `defaultdict(list)` | $O(n+m)$ | $O(\deg u)$ | 最大 | **慢 1.5–2 倍** | ❌ 竞赛里没有它的位置 |

> **一句话决策**：$n \le 10^5$ 用 `[[] for _ in range(n+1)]`，
> $n \ge 2\times10^5$ 或内存吃紧就上 CSR。**任何时候都不要 `defaultdict(list)`。**

---

## 3　度数与图的基本统计

```python
# [片段] 三种度数，一次扫边全部搞定
deg = [0] * (n + 1)                          # 无向图度数
indeg = [0] * (n + 1)                        # 有向图入度
outdeg = [0] * (n + 1)                       # 有向图出度
for u, v in edges:
    deg[u] += 1                              # 无向视角：这条边给两端各贡献 1 度
    deg[v] += 1
    outdeg[u] += 1                           # 有向视角：边从 u 出发
    indeg[v] += 1                            # 边进入 v
```

几个高频判定：

| 判定 | 条件 |
| --- | --- |
| $u$ 是树的叶子 | `deg[u] == 1`（无根树），或 `len(children[u]) == 0`（有根树） |
| 有向图的「源点」 | `indeg[u] == 0` → 拓扑排序的起点 |
| 「函数图」 | 每个点 `outdeg[u] == 1` → 一定是「尾巴 + 环」的 $\rho$ 形（BISHI98） |
| 无向图是树 | 连通 且 $m = n-1$ |
| 存在欧拉回路（无向） | 连通 且所有点度数为偶数 |

> **避免浮点的技巧**：涉及「度数的平均值」时，
> 把 $\deg(x) > \dfrac{\sum_{y \in N(x)} \deg(y)}{\deg(x)}$
> 两边同乘 $\deg(x)$ 变成 $\deg(x)^2 > \sum_{y \in N(x)} \deg(y)$，
> **全整数比较，零精度风险**。BISHI99 考的就是这个，
> 详见 [浮点与科学计数法](../toolkit/float.md)。

---

## 4　图的 BFS

队列必须是 `collections.deque`。`list.pop(0)` 是 $O(n)$，
$2\times10^5$ 个点会退化成 $4\times10^{10}$，必 TLE
（见 [队列与双端队列](../ds/queue.md)）。

```python
from collections import deque


def bfs(s, start, adj, n):
    """图的 BFS（CSR 版）。返回 dist 数组，-1 表示不可达。O(n + m)。"""
    dist = [-1] * (n + 1)                    # -1 = 还没访问过，也正好是「不可达」的输出值
    dist[s] = 0
    q = deque([s])                           # 起点先入队；deque 的两端操作都是 O(1)
    while q:
        u = q.popleft()                      # 队头一定是当前层里最早入队的点
        d = dist[u] + 1                      # u 的邻居只要是新点，距离必然是 d
        for i in range(start[u], start[u + 1]):
            v = adj[i]
            if dist[v] < 0:                  # dist 一身兼二职：距离 + 访问标记
                dist[v] = d                  # 首次访问即最短，之后不会再被改小
                q.append(v)
    return dist
```

> **BFS 天然是迭代的**，所以它是 Python 里最安全的图遍历方式。
> 「只问连通性、只问最短步数」时**一律优先 BFS**，
> 省掉所有和递归深度有关的麻烦。BFS 的完整套路见
> [BFS广度优先搜索](../search/bfs.md)。

---

## 5　图的 DFS：**必须写迭代版**

```python
# ❌ 直译 C++ 的递归 DFS
def dfs(u):
    vis[u] = 1                               # 进入即标记，防止沿着无向边走回去
    for v in adj[u]:
        if not vis[v]:
            dfs(v)                           # 每递归一层就多占一层 Python 栈和 C 栈
```

一条 $10^5$ 长的链就能把它打爆：

| 问题 | 后果 |
| --- | --- |
| CPython 默认递归上限 1000 | `RecursionError`，$n \ge 1000$ 的链必触发 |
| `sys.setrecursionlimit(300000)` | 只改计数器，**C 栈仍会溢出 → 段错误，没有任何报错信息** |
| 每层递归约 0.5 μs | 比迭代慢 2–3 倍 |

> **判据**：图上 DFS 的递归深度上界就是**点数** $n$。
> 只要 $n \ge 10^4$，就必须写迭代版。竞赛里图论题的 $n$ 几乎总是 $\ge 10^5$，
> 所以结论是：**图上 DFS 一律写迭代**。

### 模板一：只需要「进入时处理」的迭代 DFS

最常见的形态（连通块标记、可达性、染色），和 BFS 只差一个 `pop()` vs `popleft()`：

```python
def dfs_iter(s, start, adj, vis):
    """迭代 DFS：只在「首次进入」时做事。O(n + m)。

    与 BFS 的唯一区别是用栈（后进先出）而不是队列。
    注意：入栈时立刻打标记，而不是出栈时才打，否则同一个点会被重复入栈。
    """
    st = [s]                                 # 显式栈代替调用栈，深度不再受 CPython 限制
    vis[s] = 1
    while st:
        u = st.pop()                         # 取栈顶 = 最近入栈的点，这就是「深度优先」
        # ---- 在这里处理 u ----
        for i in range(start[u], start[u + 1]):
            v = adj[i]
            if not vis[v]:
                vis[v] = 1                   # ★ 入栈时就标记
                st.append(v)                 # 栈里同一时刻最多 n 个点
```

> ⚠️ **入栈即标记 vs 出栈才标记**：如果写成出栈时才 `vis[u] = 1`，
> 一个点可能被它的多个邻居重复压栈，栈长度会膨胀到 $O(m)$。
> 功能上仍对（出栈时判一下 `if vis[u]: continue`），但内存会炸。
> **入栈即标记**是标准写法。

### 模板二：需要「回溯 / 退出时处理」的迭代 DFS

求子树大小、DFS 序的 `out` 值、树形 DP 都需要「离开节点」这个时机。
把「进入」和「离开」都压进栈：

```python
def dfs_inout(root, start, adj, n):
    """带进入 / 离开两个时机的迭代 DFS。返回 (tin, tout, order, parent)。

    栈里存 (节点, 是否是「离开」事件)。也可以用负号编码省掉一个元组。
    """
    tin = [0] * (n + 1)                      # tin[u] = 进入 u 的时刻
    tout = [0] * (n + 1)                     # tout[u] = 离开 u 的时刻
    parent = [0] * (n + 1)                   # 0 = 没有父亲（根，或未访问）
    order = []                               # 进入顺序（先序）
    timer = 0                                # 全局时钟，每进入一个点走一格
    st = [(root, 0)]                         # 第二维 0 = 「进入」事件，1 = 「离开」事件
    parent[root] = 0
    vis = bytearray(n + 1)                   # bytearray 比 list 省 8 倍内存
    vis[root] = 1
    while st:
        u, leaving = st.pop()
        if leaving:                          # ---- 离开 u ----
            tout[u] = timer                  # 此刻 u 的整棵子树都已进入过
            continue
        timer += 1
        tin[u] = timer
        order.append(u)
        st.append((u, 1))                    # ★ 先压「离开」事件
                                             # 它被压在所有孩子之下，所以最后才弹出
        for i in range(start[u], start[u + 1]):
            v = adj[i]
            if not vis[v]:
                vis[v] = 1                   # 入栈即标记，同一个点不会被压两次
                parent[v] = u
                st.append((v, 0))            # 孩子的「进入」事件压在上面，先被处理
    return tin, tout, order, parent
```

> **树上还有更快的办法**：先用 BFS 求出一个「父亲一定排在儿子前面」的
> `order` 数组，再**倒着遍历 `order`** 就等价于「所有儿子处理完之后处理父亲」。
> 这样连栈都不用，全是 C 层的数组遍历。树形 DP 在 Python 里应该这么写，
> 详见 [树的基础与遍历](tree/basic.md)。

### DFS vs BFS 选型

| 需求 | 选 |
| --- | --- |
| 最短步数（无权） | **BFS** |
| 只判连通 / 数连通块 | 都行，**BFS 更省心** |
| 需要子树信息、括号序、回溯 | DFS（迭代版） |
| 需要「路径」本身（如全排列、回溯剪枝） | DFS |
| Tarjan 强连通分量 / 割点 | DFS（必须迭代改写，见 [强连通分量](scc.md) 与 [割点与桥](cut.md)） |

---

## 6　连通块

```python
def count_components(n, start, adj):
    """数连通块个数，并给每个点标上所属块编号。O(n + m)。"""
    comp = [0] * (n + 1)                     # comp[u] = u 所属块编号；0 兼任「未访问」
    size = [0]                               # size[c] = 第 c 块的点数（下标从 1 用）
                                             # 先塞一个占位元素，让下标和块号对齐
    c = 0
    for s in range(1, n + 1):                # 对每个还没归属的点各起一轮遍历
        if comp[s]:
            continue                         # 已经被前面某一轮收走了
        c += 1                               # 开一个新块
        cnt = 0                              # 这一块已经数到的点数
        st = [s]
        comp[s] = c                          # 入栈即标记（见模板一）
        while st:
            u = st.pop()
            cnt += 1
            for i in range(start[u], start[u + 1]):
                v = adj[i]
                if not comp[v]:
                    comp[v] = c
                    st.append(v)
        size.append(cnt)                     # 这一轮搜到的点恰好构成第 c 块
    return c, comp, size
```

> **`for s in range(1, n+1)` 这层外循环不能省。**
> 「保证连通」的题面可能骗人（BISHI100），而不连通的图只搜一次会漏掉整块。
> 这层循环的总代价是 $O(n)$，白送。

**连通块和并查集的分工**：

| 情形 | 用什么 |
| --- | --- |
| 图已经建好，一次性求所有连通块 | **遍历（BFS/DFS）**，$O(n+m)$，常数更小 |
| 边是**动态一条条加进来**的 | **并查集**（[并查集](../ds/dsu.md)） |
| 要求「最早何时全部连通」 | 并查集 + 排序 |
| 有**删边**操作 | 离线倒序 + 并查集 |
| **有向图**的强连通性 | Tarjan SCC，并查集无能为力 |

---

## 7　例题

<!-- CHAPTER-EXAMPLE-TABLE -->

### BISHI95 【模板】链式前向星（简单）

> 无向图 $n, m \le 10^5$，给出 $m$ 对 $a_i, b_i$。
> 输出 $n$ 行，第 $i$ 行**升序**输出与 $i$ 号点直接相连的所有点编号；
> 孤立点输出 `None`。
> 题面见 [原题](https://www.nowcoder.com/practice/23f622c8b15f4b37bffe1a986eeea185)。
> 题解见 [`solutions/nowcoder/BISHI95/sol.py`](../solutions/BISHI95.md)（已用官方样例验证）。

标题写着链式前向星，**但正确的 Python 解法是 list of list**。
理由在 §2 已经讲过：Python 里遍历链表指针比遍历 `list` 慢，
而链式前向星在这题里没有任何额外收益（它甚至还要求排序，
而链式前向星的天然顺序是**倒序**的，一样得排）。

```python
import sys


def main():
    data = sys.stdin.buffer.read().split()   # 一次读完全部输入，切成 token 列表
    n, m = int(data[0]), int(data[1])
    adj = [[] for _ in range(n + 1)]         # 定长 list of list，不用 defaultdict

    p = 2                                    # p 是 data 里的游标：前两个 token 已用掉
    for _ in range(m):
        a = int(data[p]); b = int(data[p + 1]); p += 2   # 每条边吃掉两个 token
        adj[a].append(b)
        adj[b].append(a)                     # 无向图：两个方向都加

    out = []                                 # 攒行，最后一次性输出
    for u in range(1, n + 1):
        e = adj[u]
        if e:
            e.sort()                         # 每个点单独排序，总代价 O(m log m)
            out.append(" ".join(map(str, e)))
        else:
            out.append("None")               # 孤立点，注意首字母大写；不能输出空行
    sys.stdout.write("\n".join(out) + "\n")  # n 行一次写出，只有一次系统调用


main()
```

**复杂度**：建表 $O(n+m)$，排序 $\sum_u \deg(u)\log\deg(u) \le O(m \log m)$，
输出 $O(n+m)$。$m = 10^5$ 稳过。

**三个坑**：

1. **孤立点输出 `None`**（首字母大写），不是空行。
   `if e:` 这个判断不能漏——空 list 的 `" ".join([])` 是空串，会输出空行；
2. **不做去重**。题面没说无重边，链式前向星的语义就是「如实存下每条边」，
   给了两条 $1$-$2$ 就该输出两个 `2`；自环 $a = b$ 会在 $a$ 的邻居里出现两次 $a$，
   这也是「照抄边表」的正确行为；
3. **输出必须攒起来一次 `write`**。$n = 10^5$ 行、总计 $2\times10^5$ 个数字，
   逐行 `print` 会被 IO 拖垮（见 [输入输出处理](../toolkit/io.md)）。

> **每个点单独 `sort()` 比全局排序快**：$\sum \deg\log\deg \le m\log m$，
> 而且每次排的都是小 list，Timsort 在小数组上几乎是线性的。
> 千万不要写成「先把所有 $(u,v)$ 对排序再分组」——那要多排 $2\times10^5$ 个元组。

### BISHI97 旺仔哥哥走迷宫（中等）

> $n, m \le 10^5$ 的**无向图**，第二行给出每个房间是否有陷阱（$t_i \in \{0,1\}$）。
> 问能否从 $1$ 号房**只经过安全房间**走到 $n$ 号房，输出 `Yes` / `No`。
> 题面见 [原题](https://www.nowcoder.com/practice/4b4ee516c23d4bd2b838646363b5c395)。
> 题解见 [`solutions/nowcoder/BISHI97/sol.py`](../solutions/BISHI97.md)（已用官方样例验证）。

**带点权限制的连通性判定**：把有陷阱的房间当成「不存在的点」删掉，
剩下的图上跑一次遍历即可。

[BFS 广度优先搜索](../search/bfs.md) 里给的是 BFS 版本。
这里给一份**迭代 DFS + CSR** 的版本，正好把本章两个模板都用上：

```python
import sys


def main():
    data = sys.stdin.buffer.read().split()
    n, m = int(data[0]), int(data[1])
    trap = data[2:2 + n]                     # b'0' / b'1'，不 decode 直接比 bytes
    ONE = b"1"                               # 绑成局部名，省掉循环里反复建字面量

    if trap[0] == ONE or trap[n - 1] == ONE:  # 起点或终点本身有陷阱
        sys.stdout.write("No\n")             # 连搜都不用搜
        return

    # ---- 先把边读进来，顺手过滤掉与陷阱点相关的边 ----
    us = []
    vs = []
    pu = us.append                           # 绑定方法，省掉 m 次属性查找
    pv = vs.append
    p = 2 + n                                # 跳过前两个数和 n 个陷阱标记
    for _ in range(m):
        a = int(data[p]); b = int(data[p + 1]); p += 2
        if trap[a - 1] == ONE or trap[b - 1] == ONE:   # 点号 1..n，陷阱表下标 0..n-1
            continue                         # 建表阶段就扔掉，内层循环不必再判
        pu(a)
        pv(b)

    # ---- CSR 邻接表（无向）----
    deg = [0] * (n + 2)                      # 第一趟：数度数
    for x in us:
        deg[x] += 1
    for x in vs:
        deg[x] += 1                          # 无向图，两个端点各记一次
    start = [0] * (n + 2)                    # 第二趟：度数前缀和 -> 起始下标
    acc = 0
    for i in range(1, n + 1):
        start[i] = acc                       # acc = 1..i-1 的度数之和
        acc += deg[i]
    start[n + 1] = acc                       # 哨兵，同时是 adj 的总长度
    pos = start[:]                           # 第三趟用的游标；start 保持不动
    adj = [0] * acc
    for i in range(len(us)):
        a = us[i]; b = vs[i]
        adj[pos[a]] = b; pos[a] += 1         # 填 a 的下一个空位，游标右移
        adj[pos[b]] = a; pos[b] += 1         # 反方向同理

    # ---- 迭代 DFS，入栈即标记 ----
    vis = bytearray(n + 1)                   # 陷阱点已经没有任何边，天然到不了
    vis[1] = 1
    st = [1]
    while st:
        u = st.pop()
        if u == n:                           # 到了终点就结束；n == 1 时首轮即命中
            sys.stdout.write("Yes\n")
            return
        for i in range(start[u], start[u + 1]):
            v = adj[i]
            if not vis[v]:
                vis[v] = 1                   # 入栈即标记，避免同一点被压多次
                st.append(v)
    sys.stdout.write("No\n")                 # 栈空 = 起点所在连通块搜完，仍没碰到 n


main()
```

**四个要点**：

1. **起点或终点自己有陷阱就直接 `No`**，连搜都不用搜。
   忘掉这条会从一个「不存在的点」出发，答案全错；
2. **$n = 1$ 时起点即终点**。上面代码第一轮 `u == n` 就返回 `Yes`（前提是 1 号房安全），
   逻辑天然覆盖，不需要特判；
3. **建表时就过滤陷阱点**，而不是在遍历的内层循环里判 `if trap[v]`。
   前者是 $O(m)$ 次判断，后者是 $O(m)$ 次判断 **× 每次多一个数组访问**，
   而且内层循环是热点；
4. `trap` 保持 `bytes` 不 `decode`，直接和 `b"1"` 比较——省掉 $10^5$ 次解码。

> **这题为什么可以用 DFS？** 因为它只问「能不能到」，不问「几步到」。
> 一旦问步数就必须换 BFS——DFS 找到的路径不是最短的。
> 这个区别是 [BFS 广度优先搜索](../search/bfs.md) 的核心。

### BISHI99 我朋友的朋友不是我的朋友（中等）

> $n, m \le 10^5$。$m$ 对朋友关系（**字符串**姓名，无向边）。
> 记 $\deg(x)$ 为好友数，$\operatorname{avg}(x) = \frac{\sum_{y\in N(x)}\deg(y)}{\deg(x)}$。
> 若 $\deg(x) > \operatorname{avg}(x)$ 则 $x$ 是「社牛」。按字典序输出所有社牛，无则输出 `None`。
> 题面见 [原题](https://www.nowcoder.com/practice/9656866233614f4191f5555a0cdcae4b)。

> ℹ️ `solutions/nowcoder/BISHI99/sol.py` 已存在，下面的代码与它一致，并由
> `scripts/verify_docs.py` 用**官方样例**实测通过。

这题的考点是**字符串建图 + 度数统计 + 避免浮点**，而且**不需要建邻接表**：
两遍扫边就够。它同时示范了本章两个通用技巧——「点是字符串就先映射成整数编号」
与「两边同乘化掉除法」。

**核心变形**（避免浮点的通用技巧）：

$$\deg(x) > \frac{\sum_{y\in N(x)}\deg(y)}{\deg(x)} \iff \deg(x)^2 > \sum_{y\in N(x)}\deg(y)$$

两边同乘 $\deg(x) > 0$，不改变不等号方向，且**全部变成整数比较**。

```python
import sys


def main():
    data = sys.stdin.buffer.read().split()   # 整份输入一次读完，按空白切成 bytes 列表
    m = int(data[1])                         # data[0] 是人数 n，本题用不到；data[1] 才是边数

    idx = {}                                 # 姓名(bytes) -> 编号
    names = []
    edges = []
    p = 2                                    # 前两个 token 是 n 和 m，姓名从下标 2 开始
    for _ in range(m):
        a = data[p]; b = data[p + 1]; p += 2 # 每行两个姓名，指针一次前进 2
        ia = idx.get(a, -1)                  # -1 当哨兵，比 in 判断再取值少一次哈希
        if ia < 0:
            ia = len(names); idx[a] = ia; names.append(a)   # 首次出现的名字，分配下一个编号
        ib = idx.get(b, -1)
        if ib < 0:
            ib = len(names); idx[b] = ib; names.append(b)
        edges.append((ia, ib))

    k = len(names)                           # 真正出现过的人数，可能少于题面给的 n
    deg = [0] * k
    for ia, ib in edges:                     # 第一遍：把所有人的度数统计完整
        deg[ia] += 1
        deg[ib] += 1

    nbr = [0] * k                            # nbr[x] = 邻居度数之和
    for ia, ib in edges:                     # 第二遍：此时 deg 已定稿，才能拿去累加
        nbr[ia] += deg[ib]
        nbr[ib] += deg[ia]

    # deg(x) > avg(x)  <=>  deg(x)^2 > Σ deg(邻居)，全整数比较
    res = [names[i] for i in range(k) if deg[i] * deg[i] > nbr[i]]
    if not res:
        sys.stdout.write("None\n")
        return
    res.sort()                               # bytes 排序 == 小写字母的字典序
    sys.stdout.write(b" ".join(res).decode() + "\n")


main()
```

**四个要点**：

1. **姓名先映射成整数编号**，之后全在数组上做。
   直接拿字符串当 `dict` 的 key 反复读写会慢 3–5 倍；
2. **`bytes` 不 decode 直接排序**——小写字母的字节序就是字典序，
   最后输出时才 `b" ".join(...).decode()`；
3. **两遍扫边**：第一遍统计 `deg`，第二遍才能累加邻居的 `deg`。
   一遍是做不到的（累加时对方的度数还没统计完）；
4. 度数为 0 的人 $\operatorname{avg}$ 是 $0/0$ 无定义，自然不是社牛，直接忽略。

> **「两边同乘化成整数比较」是通用武器**，凡是「$a > b/c$」形式的判定都该这么做。
> 见 [浮点与科学计数法](../toolkit/float.md)。

> 如果这题改成「删掉哪个人会让某两人失去联系」，那就是**真正的割点问题**，
> 直接把上面的 `edges` 喂给 [割点与桥](cut.md) 的 `build_undirected_csr` +
> `cut_and_bridge` 即可，**建图部分完全不用改**。

### 大纲里的 BISHI100

BISHI100「【模板】二分图染色判定」在大纲中同时挂在本章和二分图章。
它的建图部分（$n, m \le 3\times10^5$ 必须用 CSR）属于本章，
判定逻辑属于 [二分图](match/bipartite.md)，完整题解放在那里。

---

## 8　本章速查

| 要点 | 结论 |
| --- | --- |
| 读题必确认 | 有向/无向、重边、自环、是否连通、编号起点 |
| 「保证连通」 | **不可信**（BISHI100 的样例就不连通），永远对每个点起一轮 |
| 握手定理 | 无向图 $\sum \deg(v) = 2m$ → CSR 数组长 $2m$ |
| **默认存图** | `adj = [[] for _ in range(n+1)]` |
| **大图存图** | **CSR**：度数 → 前缀和 → 填充 |
| **禁用** | `defaultdict(list)`（慢 1.5–2 倍，且丢孤立点） |
| 链式前向星 | 认识即可，Python 下比 `list` 慢 |
| `i ^ 1` | 成对加边时的反向边下标（C++ 网络流常用） |
| 邻接矩阵 | 只在 $n \le 500$（Floyd）时用；**重边要取 min** |
| 点编号不连续 | 离散化成 $0..n-1$，别用 `defaultdict` |
| **图上 DFS** | **必须迭代**，递归深度上界就是 $n$ |
| 迭代 DFS | **入栈即标记**，否则栈膨胀到 $O(m)$ |
| 需要「离开」时机 | 栈里存 `(u, leaving)` 二元组 |
| 树上代替 DFS | BFS 求 `order`，**倒序遍历**即后序 |
| BFS 队列 | 必须 `deque`，`list.pop(0)` 是 $O(n)$ |
| 连通块 | 遍历 $O(n+m)$；动态加边才用并查集 |

| 规模 | Python 现实性 |
| --- | --- |
| $n, m \le 10^5$ | ✅ list of list + BFS/DFS，$O(n+m)$ 轻松 |
| $n, m \le 3\times10^5$ | ✅ **必须 CSR**，输入必须 `buffer.read().split()` |
| $n, m \le 10^6$ | ⚠️ CSR + 极简内层循环，勉强；建图本身就要 1–2 秒 |
| 邻接矩阵 $n = 1000$ | ⚠️ $10^6$ 格，光初始化 ~1 秒 |
| 邻接矩阵 $n = 5000$ | ❌ $2.5\times10^7$ 格，内存和时间双爆 |

| 看到什么 → 想到什么 |
| --- | 
| 「每个点出度为 1」→ 函数图，$\rho$ 形，一定有环 |
| 「$n-1$ 条边 + 连通」→ 树（[树的基础与遍历](tree/basic.md)） |
| 「点数很小（$\le 500$）+ 问所有点对」→ 邻接矩阵 + Floyd（[最短路](shortest-path.md)） |
| 「边一条条加入」→ 并查集（[并查集](../ds/dsu.md)） |
| 「有向 + 强连通」→ Tarjan（[强连通分量](scc.md)） |

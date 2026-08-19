# 第 60 章　DFS 深度优先搜索

> **配套例题**：BISHI76 迷宫寻路、BISHI77 数水坑、BISHI78 全排列、BISHI79 取数游戏、BISHI83 迷宫问题
> **来源**：S3 day7《简单图论》图的遍历与连通块；S3 day2《链表　DLX　并查集》暴力搜索与剪枝
> **前置**：[11-函数](../part1-python基础/11-函数.md)（递归）、[32-栈](../part3-数据结构/32-栈.md)、[21-复杂度与Python性能](../part2-竞赛基本功/21-复杂度与Python性能.md)

DFS（Depth First Search，深度优先搜索）是「**一条路走到黑，走不通再退回来换一条**」。
它是所有搜索算法的地基：回溯、记忆化搜索、剪枝、树上 DP、Tarjan、DLX，
全都是 DFS 加了点东西。

**但 DFS 是 Python 在算法竞赛里最大的一个坑。**
C++ 选手写 DFS 从不考虑深度，Python 选手写 DFS **必须先算深度**——
默认递归上限只有 1000 层，而且就算把它调大，物理栈照样会**静默崩溃**（连报错都没有）。

所以这一章的重点不是「DFS 怎么写」，而是：
**什么时候可以放心递归，什么时候必须改成迭代，以及怎么改。**

---

## 60.1　DFS 的递归框架

### 最小骨架

```python
def dfs(u):
    """访问节点 u。vis 防止重复访问，是 DFS 的灵魂。"""
    vis[u] = True               # 一进门就标记，递归返回之前不会有人再进来
    for v in adj[u]:            # 枚举 u 的所有后继
        if not vis[v]:          # 漏掉这一句，图上只要有环就会无限递归
            dfs(v)
```

三个必备部件，缺一个就会死循环或者指数爆炸：

| 部件 | 作用 | 漏掉的后果 |
| --- | --- | --- |
| `vis` 标记 | 每个状态只处理一次 | 图上有环 → **死递归**；DAG 上 → 指数级重复 |
| 后继枚举 | 定义「往哪走」 | — |
| 边界/出口 | 何时停止 | 无穷递归 |

S3 day7 里对连通块的描述就是这个骨架的直接应用：

> 使用 DFS 或者 BFS 找出所有连通块：DFS 或 BFS 的过程中**标记已经访问过的节点，避免重复访问**。时间复杂度 $\Theta(n+m)$。

### 什么时候标记 `vis`

这是最容易写错的地方，**两种时机语义完全不同**：

| 写法 | 语义 | 用途 |
| --- | --- | --- |
| 进入 `dfs(u)` 时立刻标记，且**不撤销** | 「这个点全局只访问一次」 | 连通块、可达性、拓扑序 |
| 进入时标记，**返回前撤销**（`vis[u] = False`） | 「这个点不能在当前路径上重复」 | 回溯、找所有路径、全排列 |

> ⚠️ **不撤销 = 遍历，撤销 = 枚举**。
> 把「求连通块」写成撤销版会退化成指数级枚举所有路径；
> 把「找所有路径」写成不撤销版会漏掉绝大多数方案。
> 写之前先问自己一句：**我是在「走遍全图」还是在「枚举所有可能」？**

### 网格上的 DFS

网格图是最常见的隐式图：格子是点，上下左右（或八向）相邻是边。

```python
# 四方向 / 八方向偏移量，写成常量元组，别在循环里现造
DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))       # 每项是 (行增量, 列增量)
DIR8 = ((-1, -1), (-1, 0), (-1, 1), (0, -1),    # 八连通 = 3x3 邻域去掉 (0, 0)
        (0, 1), (1, -1), (1, 0), (1, 1))


def dfs_grid(g, vis, x, y, n, m):
    """网格四连通 DFS（递归版）。仅在深度可控时使用！"""
    vis[x][y] = 1                               # 进入即标记且不撤销 = 每格只走一次
    for dx, dy in DIR4:
        nx, ny = x + dx, y + dy
        # 四个条件的先后不能换：确认下标合法之后，才敢拿它去索引 vis 和 g
        if 0 <= nx < n and 0 <= ny < m and not vis[nx][ny] and g[nx][ny] != '#':
            dfs_grid(g, vis, nx, ny, n, m)
```

> **这段代码在 Python 里是个定时炸弹。**
> $n = m = 100$ 的网格，如果整张图是一条蛇形通道，递归深度就是 $10^4$ 层——
> 远超默认的 1000。BISHI76、BISHI77 都是 $100 \times 100$，
> 所以那两题的题解**都用了显式栈**，见 60.4。

---

## 60.2　回溯：DFS 的枚举形态

回溯（backtracking）就是「**做选择 → 递归 → 撤销选择**」的 DFS。
它枚举的不是图上的点，而是**决策序列**。

### 通用模板

```python
def backtrack(path, state):
    """回溯三件套：选择 -> 递归 -> 撤销。三步一步都不能少。"""
    if is_answer(path):
        record(path[:])                  # ★ 必须复制！path 后面还要改
        return                           # 收下这一组解，本条路径到此为止
    for choice in candidates(state):
        if not ok(choice, state):        # 剪枝：不合法就别往下走
            continue
        do(choice, path, state)          # 1. 做选择
        backtrack(path, state)           # 2. 递归
        undo(choice, path, state)        # 3. 撤销：现场恢复成进入本层时的样子
```

> ⚠️ **`record(path[:])` 里的切片不能省。** `path` 是同一个 list 对象，
> 回溯过程中它会被反复修改；直接 `record(path)` 存进去的是**引用**，
> 最后拿到的会是一堆指向同一个空列表的引用。
> 这是回溯题最高频的 bug，见 [05-列表](../part1-python基础/05-列表.md) 的复制陷阱。

### 三大枚举：排列 / 子集 / 组合

这三个是回溯的「Hello World」，务必背下来它们的**结构差异**。

| 枚举对象 | 数量 | 关键控制 |
| --- | --- | --- |
| **排列** | $n!$ | `used[]` 标记，每层从头扫 |
| **子集** | $2^n$ | 每个元素「选 / 不选」，或按起点 `start` 递增 |
| **组合** $C(n,k)$ | $\binom{n}{k}$ | 按起点 `start` 递增，选够 $k$ 个就收 |

```python
def permutations_dfs(n):
    """1..n 的全排列，按字典序输出。O(n! * n)。"""
    res = []
    path = []                                    # 当前已经确定的前几位
    used = [False] * (n + 1)                     # used[v]：v 是否已经出现在 path 里
                                                 # 开 n+1 格，下标直接用 1..n，不做偏移

    def dfs():
        if len(path) == n:
            res.append(path[:])                  # 复制！path 是同一个对象，之后还会被改
            return
        for v in range(1, n + 1):                # 从小到大 -> 天然字典序
            if used[v]:
                continue                         # 排列里每个数只能出现一次
            used[v] = True
            path.append(v)
            dfs()
            path.pop()                           # 撤销
            used[v] = False                      # 撤销：v 换到别的位置上还要再用
    dfs()
    return res


def subsets_dfs(a):
    """a 的所有子集，O(2^n * n)。按「起点递增」写，天然不重不漏。"""
    n = len(a)
    res = []
    path = []

    def dfs(start):
        res.append(path[:])                      # 每个节点都是一个子集，根节点是空集
        for i in range(start, n):                # 只从 start 往后挑，同一子集不会被换序枚举
            path.append(a[i])
            dfs(i + 1)                           # ★ i+1：后面的元素只能选更靠后的
            path.pop()                           # 撤销，换下一个 i
    dfs(0)
    return res


def combinations_dfs(n, k):
    """从 1..n 中选 k 个的所有组合。"""
    res = []
    path = []

    def dfs(start):
        if len(path) == k:
            res.append(path[:])
            return
        # 剪枝：还差 k-len(path) 个数，i 最大只能取到 n-(k-len(path))+1；
        # range 的右端是开区间，所以写成 +2
        for i in range(start, n - (k - len(path)) + 2):
            path.append(i)
            dfs(i + 1)                           # 下一层从 i+1 起，组合不计顺序
            path.pop()
    dfs(1)                                       # 元素编号是 1..n，所以起点取 1
    return res
```

### 但在 Python 里：先想想 `itertools`

**这是本教程反复强调的取舍。** `itertools` 的循环在 C 层跑，
比手写 Python 递归快一个数量级：

| 手写回溯 | `itertools` 等价物 | 相对速度 |
| --- | --- | --- |
| `permutations_dfs(n)` | `itertools.permutations(range(1, n+1))` | **约 10–30×** |
| `combinations_dfs(n, k)` | `itertools.combinations(a, k)` | **约 10–30×** |
| `subsets_dfs(a)` | `chain.from_iterable(combinations(a, r) for r in range(len(a)+1))` | 约 10× |
| 笛卡尔积（每位独立选） | `itertools.product(opts, repeat=n)` | 约 10× |
| $2^n$ 子集（位运算枚举） | `for s in range(1 << n): ...` | 见 [46-位运算](../part4-基础算法/46-位运算.md) |

> **判据**：如果枚举**没有剪枝**（要枚举出全部方案），一律用 `itertools`；
> 如果枚举**必须靠剪枝才能跑完**（比如 N 皇后、数独），就得手写回溯——
> 因为 `itertools` 没法在中途「掐断一整个分支」。
>
> BISHI78 全排列就是前者，题解直接用了 `itertools.permutations`。

---

## 60.3　连通块与泛洪填充

「数有多少个岛 / 水坑 / 联通区域」是 DFS 最经典的应用：

```python
def count_components(g, n, m, target, dirs):
    """数网格中值为 target 的连通块个数。dirs 传 DIR4 或 DIR8。O(nm)。"""
    vis = [bytearray(m) for _ in range(n)]       # 每格 1 字节，比 list of bool 省内存
    cnt = 0
    for si in range(n):
        for sj in range(m):
            if g[si][sj] != target or vis[si][sj]:
                continue                         # 不是目标格，或已属于前面数过的块
            cnt += 1                             # 每找到一个新起点，就是一个新连通块
            vis[si][sj] = 1
            stack = [(si, sj)]                   # 显式栈，不用递归
            while stack:
                x, y = stack.pop()
                for dx, dy in dirs:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < n and 0 <= ny < m \
                            and not vis[nx][ny] and g[nx][ny] == target:
                        vis[nx][ny] = 1          # ★ 入栈即标记
                        stack.append((nx, ny))
    return cnt
```

> **「入栈即标记」是迭代 DFS/BFS 的铁律。**
> 如果改成「出栈时才标记」，同一个格子会被它的 4（或 8）个邻居各压一次，
> 栈的规模会从 $O(nm)$ 膨胀到 $O(8nm)$，还可能重复计数。

**连通块题的常见变体**：

| 变体 | 改动 |
| --- | --- |
| 求最大连通块面积 | 在遍历时累加 `size` |
| 求连通块的外接矩形 | 维护 `minr/maxr/minc/maxc`（BISHI81） |
| 判块是否为实心矩形 | `size == (maxr-minr+1)*(maxc-minc+1)`（BISHI81） |
| 八连通 | 方向数组换成 `DIR8`（BISHI77） |
| 每个块要回答多次询问 | 给每个格子打上「块编号」，预处理块大小 |
| 只问「起点能否到终点」 | 不用数块，一次泛洪即可（BISHI76） |

---

## 60.4　递归改迭代

**这一节是本章的核心，也是 Python 选手必须过的一关。**

### 为什么必须改：三层限制

**第一层：解释器软限制 = 1000。**

```python
import sys
print(sys.getrecursionlimit())        # 1000
```

超过就抛 `RecursionError`，这是**能捕获、有报错**的，还算友好。

**第二层：物理 C 栈。** `sys.setrecursionlimit(10**6)` 只是把计数器调大，
**并不会给你更多的栈空间**。每一层 Python 函数调用都要在 C 栈上放一个求值帧，
撞破 C 栈的结果是**进程直接被操作系统杀掉**：没有异常、没有 traceback、
在牛客上表现为「运行错误」甚至「输出为空」，极难定位。

本机（Windows + CPython 3.9）实测：

| 环境 | 栈大小 | 裸递归可达深度 |
| --- | --- | --- |
| 主线程（Windows 默认） | 1 MB | **约 2500–2800 层就静默崩溃** |
| 主线程（Linux 判题机常见） | 8 MB | 约 2 万层 |
| `threading.stack_size(1 << 26)` 新线程 | 64 MB | **7 万层以上没问题** |

> **换算**：每层递归约吃掉 **0.4–1 KB** 的 C 栈（函数局部变量越多越吃）。
> 想要 $10^5$ 层深度，至少要准备 64 MB 以上的栈。

**第三层：速度。** 一次 Python 函数调用约 0.1 μs，$10^6$ 次递归光调用开销就接近 1 秒。
详见 [21-复杂度与Python性能](../part2-竞赛基本功/21-复杂度与Python性能.md)。

### `setrecursionlimit` vs `threading.stack_size`

**这两个东西解决的是完全不同的问题，必须一起用。**

| | `sys.setrecursionlimit(N)` | `threading.stack_size(N)` |
| --- | --- | --- |
| 改的是什么 | 解释器的**计数器上限**（软限制） | 新线程的**物理栈字节数**（硬限制） |
| 不改的后果 | `RecursionError`（有报错） | **段错误/静默崩溃**（无报错） |
| 对主线程有效吗 | ✅ 有效 | ❌ **无效**，只对之后创建的线程生效 |
| 单独用够不够 | ❌ 不够，仍会崩 | ❌ 不够，仍会 `RecursionError` |

**正确的「开大栈」写法**（两个都要设，且必须新起线程）：

```python
import sys
import threading


def main():
    sys.setrecursionlimit(300000)             # 1. 解除软限制
    ...                                       #    在这里写递归逻辑


threading.stack_size(1 << 26)                 # 2. 64 MB 物理栈（必须在 Thread 创建前调用）
t = threading.Thread(target=main)
t.start()
t.join()                                      # 等子线程跑完；主线程先退出会截断输出
```

> **三个细节**：
> 1. `threading.stack_size` 必须在 `Thread(...)` **构造之前**调用，之后调用无效；
> 2. 有些评测机对线程栈大小有上限，`1 << 26`（64 MB）是比较安全的取值，
>    盲目开到 `1 << 30` 可能直接 `ThreadError: can't start new thread`；
> 3. **`sys.setrecursionlimit` 要在线程内部（或至少在 `start()` 之前）设**，
>    它是解释器全局的，设一次即可。

### 改法一：纯遍历型 DFS → 直接换成显式栈

只在「进入节点」时做事、不需要「回来之后再做事」的 DFS，改写是**机械的**：

```python
# ---- 递归版 ----
def dfs(u):
    vis[u] = 1                            # 进入时标记且不撤销 = 全局只访问一次
    for v in adj[u]:
        if not vis[v]:
            dfs(v)                        # 递归深度 = 最长路径长度，随时可能爆栈


# ---- 迭代版（等价，深度不受限）----
def dfs_iter(s):
    vis[s] = 1                            # 起点压栈之前先标记，与下面的规则保持一致
    stack = [s]
    while stack:
        u = stack.pop()                   # 后进先出，效果就是「一条路走到黑」
        for v in adj[u]:
            if not vis[v]:
                vis[v] = 1                # ★ 入栈即标记
                stack.append(v)
```

> **访问顺序会变**：递归版按 `adj[u]` 的正序深入，迭代版因为栈是后进先出，
> 实际是按**逆序**深入。如果题目对遍历顺序敏感（比如要求字典序最小的 DFS 序），
> 就要 `for v in reversed(adj[u])`。**只求连通性/可达性时顺序无所谓。**

### 改法二：需要「回来之后再做事」→ 两趟法

树上 DP、求子树大小、求 DFS 序……这类需要**后序**处理的问题，
不能简单换成显式栈。**最好用的写法是「两趟法」**：
第一趟只求出访问顺序和父亲，第二趟**倒着扫一遍**就是后序。

```python
def tree_dp_two_pass(n, adj, root=1):
    """树上后序 DP 的迭代写法。O(n)，深度不受限。

    第一趟：BFS/DFS 求出 order（访问顺序）和 par（父亲）；
    第二趟：reversed(order) 即为后序，儿子一定先于父亲被处理。
    """
    par = [0] * (n + 1)                    # par[v] = v 的父亲；0 表示「没有父亲」
    order = []                             # 第一趟的访问顺序，也就是一个合法的 DFS 序
    stack = [root]
    par[root] = 0                          # 根没有父亲，用 0 当哨兵
    vis = bytearray(n + 1)
    vis[root] = 1
    while stack:
        u = stack.pop()
        order.append(u)
        for v in adj[u]:
            if not vis[v]:                 # 无根树的邻接表不分方向，靠 vis 挡住「走回父亲」
                vis[v] = 1                 # ★ 入栈即标记
                par[v] = u
                stack.append(v)

    size = [1] * (n + 1)                   # 每个点先把自己算进子树大小
    for u in reversed(order):              # ★ 倒序 = 后序：儿子已经算完了
        p = par[u]
        if p:                              # 根的父亲是 0，到根就停，不再往外累加
            size[p] += size[u]
    return size, order, par
```

> **这是 Python 里写树上 DP 的标准姿势**，比任何状态机写法都简洁。
> 记住这句话：**「reversed(DFS 序) 就是后序」**。
> 见 [94-树上算法](../part8-图与树/94-树上算法.md)、
> [103-区间树形状压DP](../part9-动态规划/103-区间树形状压DP.md)。

### 改法三：真正需要「进入/退出」两个时机 → 事件栈

Tarjan、求 DFS 括号序、需要在退出时撤销现场的场合，用「**状态机栈**」：

```python
def dfs_events(s, adj):
    """栈里存 (节点, 阶段)。阶段 0 = 进入，阶段 1 = 退出。"""
    vis = {}
    stack = [(s, 0)]
    while stack:
        u, stage = stack.pop()
        if stage == 0:
            if u in vis:
                continue                    # 同一点可能被多个邻居压入，靠这一句去重
            vis[u] = True                   # 这里只能出栈时标记，理由见下方说明
            stack.append((u, 1))            # ★ 先压「退出事件」：它会在所有孩子之后才弹出
            for v in reversed(adj[u]):      # 逆序压栈以保持正序访问
                if v not in vis:
                    stack.append((v, 0))
            # ---- 在这里写「进入 u 时」要做的事 ----
        else:
            pass
            # ---- 在这里写「离开 u 时」要做的事（后序）----
```

> **事件栈是「入栈即标记」的唯一例外**：进入事件和退出事件必须成对，
> 而退出事件只能在真正展开 $u$ 时才压得进去，所以标记只能推迟到出栈那一刻。
> 代价是同一个点可能被压入多次，栈的规模比改法一大，靠 `if u in vis: continue` 兜住。

另一种等价写法是「**迭代器栈**」，更接近递归的语义（能保留「循环走到哪了」）：

```python
def dfs_iterstack(s, adj):
    """栈里存 (节点, 该节点的邻居迭代器)。最贴近递归语义的迭代改写。"""
    vis = {s}
    stack = [(s, iter(adj[s]))]             # 迭代器替我们记住「这一层的循环走到哪了」
    while stack:
        u, it = stack[-1]                   # 只看栈顶不弹出，这一层可能还没走完
        advanced = False
        for v in it:                        # 从上次断点继续
            if v not in vis:
                vis.add(v)                  # ★ 入栈即标记
                stack.append((v, iter(adj[v])))
                advanced = True
                break                       # 立刻下潜；剩下的邻居等回到这一层再走
        if not advanced:
            stack.pop()                     # 邻居全部走完，这一层才真正出栈
            # ---- 这里是「离开 u」，后序位置 ----
```

| 改法 | 适用 | 优点 | 缺点 |
| --- | --- | --- | --- |
| 显式栈（改法一） | 只需前序 / 只求可达性 | 最简单最快 | 拿不到后序 |
| **两趟法（改法二）** | **树 / DAG 上的后序 DP** | **最快、最好写** | 需要先存下整个访问序 |
| 事件栈（改法三） | 需要进入+退出两个时机 | 通用 | 栈元素多一倍，常数大 |
| 迭代器栈 | 需要保留「循环进度」 | 语义最贴近递归 | 迭代器对象开销大，最慢 |

### 决策表：到底该不该递归

| 最大递归深度 | 建议 |
| --- | --- |
| $\le 900$ | ✅ **直接递归**，什么都不用做 |
| $\le 10^4$ | ⚠️ `setrecursionlimit` + **开 64 MB 线程栈** |
| $\le 10^5$ | ⚠️ 同上，但已经很险（时间也可能不够）；**优先改迭代** |
| $> 10^5$ | ❌ **必须改迭代**，没有第二条路 |
| **深度未知/取决于数据** | ❌ **一律按最坏情况算**：链状树、蛇形迷宫都是 $O(n)$ 深 |

> **实战建议**：竞赛里遇到图/树/网格的 DFS，
> **直接上迭代版**，不要先写递归再等着 RE。
> 迭代版只多写三行，却省掉了一整类不可调试的崩溃。

---

## 60.5　DFS 的复杂度

| 场景 | 复杂度 |
| --- | --- |
| 图的遍历（邻接表） | $O(n + m)$ |
| 网格泛洪 | $O(nm)$，四连通常数 4，八连通常数 8 |
| 全排列枚举 | $O(n! \cdot n)$ |
| 子集枚举 | $O(2^n \cdot n)$ |
| 带剪枝的搜索 | **无法用大 O 描述**，只能估「搜索树节点数」 |

最后一行是搜索题的本质：**剪枝的好坏决定生死**，见
[62-记忆化搜索与剪枝](62-记忆化搜索与剪枝.md)。

S3 day2 讲 DLX（Dancing Links X，用双向十字链表实现的精确覆盖搜索）时给的搜索流程，就是「剪枝驱动的 DFS」的典范：

> 1. 如果当前矩阵没有列，则要求满足。
> 2. 任意选取一列，如果这一列上没有 1，则**无解**（← 可行性剪枝）。
> 3. 否则依次遍历这一列上所有有 1 的行，其中必须有一行被选中。钦定某一行被选中，删去所有被覆盖的列和不能再选择的行，得到一个更小的矩阵，递归下去处理。

其中「选哪一列」用**当前 1 最少的列**（$S$ 启发式）能把搜索树砍掉几个数量级——
这就是 DLX 快的全部秘密。见
[115-高级搜索与精确覆盖](../part10-进阶专题/115-高级搜索与精确覆盖.md)。

---

## 60.6　例题

### BISHI76 迷宫寻路（简单）

> $n \times m \le 100 \times 100$ 的迷宫，`.` 是空地、`#` 是墙，四连通移动。
> 问能否从左上角 $(1,1)$ 走到右下角 $(n,m)$。输出 `Yes` / `No`。
> 题面见 [BISHI76 原题（牛客）](https://www.nowcoder.com/practice/0c8930e517444d04b426e9703d483ed4)。
> 题解见 [`solutions/BISHI76.py`](../solutions/BISHI76.md)（已用官方样例验证）。

最裸的连通性判定。只问「能不能到」，不问步数，所以 DFS / BFS / 并查集都行，
本质是一次泛洪填充。

**Python 的关键判断**：$nm = 10^4$，最坏情况（蛇形通道）递归深度就是 $10^4$ 层，
**远超默认的 1000**。所以这里**必须写显式栈**。

```python
import sys


def main():
    data = sys.stdin.buffer.read().split()
    n, m = int(data[0]), int(data[1])
    g = data[2:2 + n]                       # 每行一个 bytes，g[i][j] 取出来是 int

    WALL = ord('#')                         # 在 bytes 上索引得到 int，所以取字符的码值
    if g[0][0] == WALL or g[n - 1][m - 1] == WALL:
        sys.stdout.write("No\n")             # 起点或终点是墙，连搜都不用搜
        return

    vis = [bytearray(m) for _ in range(n)]  # 每格 1 字节
    vis[0][0] = 1                           # 起点压栈之前先标记
    stack = [(0, 0)]                        # 显式栈，深度不受解释器限制
    ok = False
    while stack:
        x, y = stack.pop()
        if x == n - 1 and y == m - 1:       # 出栈时判终点，n = m = 1 时第一次就命中
            ok = True
            break                           # 只问能否到达，找到就可以停
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            # 先判越界再索引：and 的短路保证不会拿非法下标去取 vis 和 g
            if 0 <= nx < n and 0 <= ny < m and not vis[nx][ny] and g[nx][ny] != WALL:
                vis[nx][ny] = 1             # 入栈即标记
                stack.append((nx, ny))
    sys.stdout.write("Yes\n" if ok else "No\n")


main()
```

复杂度 $O(nm) = 10^4$，毫秒级。

**三个坑**：

1. **$n = m = 1$ 时起点就是终点**，答案是 `Yes`。上面的代码在第一次 `pop` 时
   就会命中 `x == n-1 and y == m-1`，天然正确——但如果你把判定写在「入栈时」
   就会漏掉起点；
2. 迷宫每行是**不含空格的字符串**，`split()` 按 token 读正好一行一个，
   不需要按行读；
3. **在 `bytes` 上索引得到的是 `int` 不是 `str`**，所以要拿 `ord('#')` 去比。
   这是 `bytes` 处理的通用注意点，见 [70-字符串处理](../part6-字符串/70-字符串处理.md)。

### BISHI77 数水坑（简单）

> $N \times M \le 100 \times 100$ 的田地，`W` 是水、`.` 是干地。
> **八连通**的水格属于同一个水坑。求水坑数量。
> 题面见 [BISHI77 原题（牛客）](https://www.nowcoder.com/practice/664ca4289fcf457ba3109fdf4a7a1a05)。
> 题解见 [`solutions/BISHI77.py`](../solutions/BISHI77.md)（已用官方样例验证）。

连通块计数模板。唯一和常规题不同的是**八连通**——
方向数组写成 4 个，会把斜着搭在一起的水格错拆成两块。

```python
import sys


def main():
    data = sys.stdin.buffer.read().split()
    n, m = int(data[0]), int(data[1])
    g = data[2:2 + n]
    W = ord('W')

    vis = [bytearray(m) for _ in range(n)]
    cnt = 0
    for si in range(n):
        row = g[si]                         # 把本行绑成局部名，内层少一次二维索引
        vrow = vis[si]
        for sj in range(m):
            if row[sj] != W or vrow[sj]:
                continue                    # 不是水，或已属于前面数过的水坑
            cnt += 1                        # 发现一个新水坑
            vrow[sj] = 1
            stack = [(si, sj)]              # 显式栈：一个水坑最多 1e4 格，递归必崩
            while stack:
                x, y = stack.pop()
                for dx in (-1, 0, 1):       # 八连通 = 3x3 邻域去掉自己
                    nx = x + dx
                    if nx < 0 or nx >= n:
                        continue            # 行号越界，这一整行的 3 个方向一起跳过
                    gr, vr = g[nx], vis[nx]  # 取一次行对象，内层 3 次列判断共用
                    for dy in (-1, 0, 1):
                        ny = y + dy
                        # dx = dy = 0 枚举到的是自己，但它已被标记，被 not vr[ny] 挡掉
                        if 0 <= ny < m and not vr[ny] and gr[ny] == W:
                            vr[ny] = 1      # 入栈即标记，防止重复入栈
                            stack.append((nx, ny))
    sys.stdout.write("%d\n" % cnt)


main()
```

复杂度 $O(8NM)$，$10^4$ 个格子，毫秒级。

**两个坑**：

1. **八连通用 `dx, dy` 双重循环枚举 $3\times3$ 邻域**（含 `(0,0)` 自己，
   但自己已经被标记过，会被 `not vr[ny]` 挡掉），比写 8 个偏移量更短；
2. 最坏情况整张图全是 `W`，一个连通块 $10^4$ 个格子，
   **递归版必 `RecursionError`**——这就是为什么这里用显式栈。

### BISHI78 全排列（简单）

> 给定 $n \le 9$，按**字典序**输出 $1 \sim n$ 的所有排列，每行 $n$ 个数用空格分隔。
> 题面见 [BISHI78 原题（牛客）](https://www.nowcoder.com/practice/1d1fe38275da44b5848add89f9e223b1)。
> 题解见 [`solutions/BISHI78.py`](../solutions/BISHI78.md)（已用官方样例验证）。

DFS 回溯的入门模板题——**但正解不是手写回溯**。

$n = 9$ 时有 $9! = 362880$ 行，总输出约 6.5 MB，
**真正的瓶颈在 IO，不在搜索**。而 `itertools.permutations`
对已排好序的输入产出的顺序**就是字典序**，且循环在 C 层跑：

```python
import sys
from itertools import permutations


def main():
    n = int(sys.stdin.buffer.read().split()[0])
    digits = [str(i) for i in range(1, n + 1)]      # 已升序 -> 排列即字典序；预转 str
    join = " ".join                                 # 绑成局部名，36 万次调用省下属性查找
    # 全部拼成一整块再一次写出：逐行 print 会把时间全花在 IO 上
    sys.stdout.write("\n".join(map(join, permutations(digits))) + "\n")


main()
```

**三个坑**：

1. **绝对不能 `for p in ...: print(p)`**——36 万次 `print` 会把时间全耗在 IO 上。
   必须先 `"\n".join` 拼成一整块再一次 `write`；
2. **预先把 `1..n` 转成 `str`**，`join` 时就不用反复 `map(str, ...)`；
3. `itertools.permutations` 的字典序性质**依赖输入本身有序**。
   如果输入是 `[3,1,2]`，产出的顺序就不是字典序了，必须先 `sorted`。

> **手写回溯版**（60.2 的 `permutations_dfs`）在 $n=9$ 时也能过
> （时限「其他语言 6 秒」很宽），但慢 10 倍以上。
> **这题的教学价值恰恰在于：会写回溯 ≠ 应该用回溯。**
> 递归深度只有 $n \le 9$ 层，所以这题**不存在递归深度问题**——
> 这是少数可以放心递归的场合。

### BISHI79 取数游戏（中等）

> $T \le 20$ 组数据，每组给 $N \times M \le 6 \times 6$ 的非负整数矩阵，
> 取出若干数使得任意两个数不**八连通**相邻，求最大和。
> 题面见 [BISHI79 原题（牛客）](https://www.nowcoder.com/practice/b002b8eb564245fdbb8a02db8dcf03e4)。
> 题解见 [`solutions/BISHI79.py`](../solutions/BISHI79.md)（已用官方样例验证）。

**这题是「搜索 vs DP」的分水岭**，值得细读。

朴素 DFS 逐格枚举「选 / 不选」是 $2^{36}$，纯搜索必挂。加上剪枝呢？
可行性剪枝（不能和已选的相邻）能砍掉很多，但最坏情况仍然不可控。

**正解是状压 DP**（本质是「按行记忆化的搜索」）。关键观察：

> 八连通相邻只会发生在「**同一行相邻列**」和「**相邻两行且列号差 $\le 1$**」，
> 隔一行以上的两个格子永远不相邻。

于是把「本行选了哪些列」压成 $M$ 位二进制 `mask`，行与行之间的约束**只依赖前一行**：

| 约束 | 判定式 |
| --- | --- |
| 行内不相邻 | `mask & (mask << 1) == 0` |
| 与上一行不八连通相邻 | `(m1 \| (m1 << 1) \| (m1 >> 1)) & m2 == 0` |

第二个式子很妙：把上一行的 mask 向左右各扩一位，**一次与运算同时覆盖了
正上方和两个斜上方**三种冲突。

```python
import sys


def main():
    data = sys.stdin.buffer.read().split()
    p = 0
    t = int(data[p]); p += 1
    out = []
    for _ in range(t):
        n, m = int(data[p]), int(data[p + 1]); p += 2
        rows = []
        for _ in range(n):
            rows.append([int(v) for v in data[p:p + m]])
            p += m

        full = 1 << m                # m 位二进制，共 2^m 种「本行选法」
        masks = [s for s in range(full) if not (s & (s << 1))]   # 行内合法：无相邻两位同为 1
        spread = [s | (s << 1) | (s >> 1) for s in range(full)]  # 向左右各扩一位

        dp = [0] * full              # dp[mask]：上一行选 mask 时的最大和
        alive = [0]                  # 上一行取空集作为哨兵起点
        for r in range(n):
            row = rows[r]
            val = {}
            for s in masks:          # 预处理本行每个 mask 的权值和
                tot = 0
                x = s
                while x:
                    low = x & -x     # lowbit：取出 x 最低位的那个 1，见 46-位运算
                    tot += row[low.bit_length() - 1]   # 该 1 在第几位就加第几列的数
                    x ^= low         # 抹掉这一位，循环次数 = 1 的个数
                val[s] = tot
            ndp = [-1] * full        # 本行的新表，-1 表示这个 mask 无法从上一行到达
            for s2 in masks:
                best = -1
                for s1 in alive:
                    if spread[s1] & s2:
                        continue     # 扩位后仍相交 = 正上方或斜上方冲突
                    if dp[s1] > best:
                        best = dp[s1]
                if best >= 0:        # 至少存在一个合法的上一行搭配
                    ndp[s2] = best + val[s2]
            dp = ndp
            alive = [s for s in masks if dp[s] >= 0]   # 只留可达的 mask，下一行少枚举
        out.append(str(max(dp)))
    sys.stdout.write("\n".join(out) + "\n")


main()
```

$M = 6$ 时子集只有 64 个，行内合法的只有 21 个（是斐波那契数 $F_8$）。
复杂度 $O(T \cdot N \cdot 21^2) < 6\times10^4$，瞬间出结果。

**三个坑**：

1. **多组数据每组都要重置 `dp`**，别把上一组的结果带进来；
2. `mask << 1` 可能超出 $M$ 位，但与 `mask2` 相与时高位天然是 0，无害；
   `mask >> 1` 在 Python 里对非负整数完全安全；
3. `alive` 列表用来跳过「上一行不可达的 mask」（`dp == -1`），
   否则会把 $-1$ 当成合法值传下去。

> **这题给出的判据**：搜索题看到「$N, M \le 6$」这种**小到离谱**的范围，
> 通常意味着**要按某一维压缩状态**，而不是真的让你暴力搜。
> 详见 [103-区间树形状压DP](../part9-动态规划/103-区间树形状压DP.md)。

### BISHI83 迷宫问题（中等）

> $h \times w \le 100 \times 100$ 的 01 迷宫（0 空地、1 墙），
> 输出一条从 $(0,0)$ 到 $(h-1,w-1)$ 的可行路径，每行 `(x,y)`。
> **保证可行路径存在且唯一**。
> 题面见 [BISHI83 原题（牛客）](https://www.nowcoder.com/practice/cf24906056f4488c9ddb132f317e03bc)。
> 题解见 [`solutions/BISHI83.py`](../solutions/BISHI83.md)（已用官方样例验证，用的是 BFS 版）。

这题是**「输出路径」类问题的模板**。核心技巧：**前驱数组 `pre[]`**。

不管是 DFS 还是 BFS，只要在「第一次访问 $v$」时记下 `pre[v] = u`，
最后从终点顺着 `pre` 一路倒推回起点，再 `reverse` 就是路径。

这里给 **DFS（显式栈）版本**，和 `solutions/` 里的 BFS 版互为对照
（题目保证路径唯一，所以两者输出相同）：

```python
import sys


def main():
    data = sys.stdin.buffer.read().split()
    h, w = int(data[0]), int(data[1])
    g = data[2:2 + h * w]                 # b'0' / b'1'，按 token 读

    WALL = b'1'                           # g 的元素是一个个 bytes token，直接与 b'1' 比
    n = h * w                             # 二维压一维：下标 = x * w + y
    pre = [-2] * n                        # -2 未访问，-1 起点，其余为前驱下标
    start, goal = 0, n - 1                # (0,0) 与 (h-1,w-1) 压一维后的下标
    pre[start] = -1                       # 起点前驱设 -1，倒推时用它当终止条件
    stack = [start]                       # ★ 显式栈：路径最长 1e4，递归必崩
    while stack:
        u = stack.pop()
        if u == goal:
            break                         # 题目保证路径唯一，摸到终点就可以收工
        x, y = divmod(u, w)               # 还原行列，只用于判四个方向是否越界
        if x > 0:                         # 不在第 0 行才能往上走
            v = u - w
            if pre[v] == -2 and g[v] != WALL:
                pre[v] = u; stack.append(v)   # ★ 入栈即记前驱，pre 同时充当 vis
        if x + 1 < h:                     # 不在最后一行才能往下走
            v = u + w
            if pre[v] == -2 and g[v] != WALL:
                pre[v] = u; stack.append(v)
        if y > 0:                         # 不在第 0 列才能往左走
            v = u - 1
            if pre[v] == -2 and g[v] != WALL:
                pre[v] = u; stack.append(v)
        if y + 1 < w:                     # 不在最后一列才能往右走
            v = u + 1
            if pre[v] == -2 and g[v] != WALL:
                pre[v] = u; stack.append(v)

    path = []
    u = goal
    while u != -1:                        # 从终点顺着 pre 倒推回起点，-1 是起点标志
        x, y = divmod(u, w)
        path.append("(%d,%d)" % (x, y))
        u = pre[u]
    path.reverse()                        # ★ 倒推出来是「终点 -> 起点」，翻回正序
    sys.stdout.write("\n".join(path) + "\n")


main()
```

**四个坑**：

1. **`pre` 数组一身兼两职**：`-2` 当「未访问」标记，其余值当前驱。
   省掉一个 `vis` 数组，也少一次数组访问；
2. **二维压成一维**（`idx = x * w + y`），用 `divmod` 还原。
   一维数组比 list of list 快，而且前驱只需存一个整数；
3. **输出格式以样例为准**。题面「输出描述」写的是「输出两个整数 $x_i, y_i$」，
   但样例输出是**带括号无空格**的 `(x,y)`。**样例和文字描述冲突时，永远信样例**；
4. 回溯出来的路径是「终点 → 起点」，**最后必须 `reverse`**。

> **DFS 找路径 vs BFS 找路径**：
> - 题目问「**任意**一条路径」→ 两者都行，DFS 常数略小；
> - 题目问「**最短**路径」→ **必须 BFS**，DFS 找到的路径不保证最短
>   （见 [61-BFS广度优先搜索](61-BFS广度优先搜索.md)）；
> - 题目问「**所有**路径」→ 回溯（要撤销 `vis`），注意可能指数爆炸。
>
> 这题因为「保证路径唯一」，三种说法碰巧一致，
> 所以是一道很好的对照练习题。

---

## 60.7　本章速查

| 要点 | 结论 |
| --- | --- |
| DFS 三件套 | `vis` 标记 + 后继枚举 + 出口 |
| `vis` 不撤销 | **遍历**：连通块、可达性 |
| `vis` 撤销 | **枚举**：回溯、所有路径 |
| 回溯三件套 | 选择 → 递归 → **撤销** |
| 存答案 | **必须 `path[:]` 复制**，否则全是同一个引用 |
| 全排列/组合 | 优先 `itertools`，快 10–30× |
| 手写回溯的价值 | 只有在**需要中途剪枝**时才不可替代 |
| 入栈时机 | **入栈即标记 `vis`**，不是出栈才标记 |
| 默认递归上限 | **1000** |
| `setrecursionlimit` | 只改**软**计数器，**不给栈空间** |
| 主线程物理栈 | Windows 1 MB ≈ **2500 层**；Linux 8 MB ≈ 2 万层 |
| `threading.stack_size(1<<26)` | 64 MB ≈ **7 万层**；必须在建 Thread **之前**调用 |
| 崩栈的表现 | **无 traceback 的静默崩溃**，最难调 |
| 深度 $\le 900$ | 放心递归 |
| 深度 $\ge 10^5$ | **必须改迭代** |
| 深度未知 | **按最坏（链/蛇形）算**，即 $O(n)$ |
| 纯前序 DFS 改写 | 显式栈，注意访问顺序会反 |
| **后序 DFS 改写** | **两趟法：`reversed(DFS 序)` 就是后序** |
| 进入+退出都要 | 事件栈 `(node, stage)` 或迭代器栈 |
| 输出路径 | `pre[]` 前驱数组 + 倒推 + `reverse` |
| 网格题 | 二维压一维 + 四周哨兵，省边界判断 |

| 看到什么 → 想到 DFS |
| --- |
| 「有多少个连通块 / 岛屿 / 水坑」 |
| 「能否从 A 到 B」（不问步数） |
| 「输出所有方案 / 全排列 / 子集」 |
| 「树上每个子树的 XXX」→ 两趟法后序 |
| 「$n \le 20$，枚举所有情况」 |
| 「棋盘上放 K 个互不攻击的棋子」→ 回溯 + 剪枝，或状压 DP |

| 看到什么 → **不要**用 DFS |
| --- |
| 「最少步数 / 最短路径」→ **BFS**（[61 章](61-BFS广度优先搜索.md)） |
| 「所有方案数」且规模大 → **DP**（[100 章](../part9-动态规划/100-DP入门.md)） |
| 深度可能上 $10^5$ 又必须后序 → **两趟法**，不是递归 |

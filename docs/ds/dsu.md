---
id: ds/dsu
title: 并查集
volume: 1
lang: py
---

# 第 38 章　并查集

<!-- CHAPTER-EXAMPLES -->
> **前置**：[序列与数组](array.md)

一个足够简洁的定义：

> 并查集原名**不相交集合数据结构**。并查集是它支持的操作的名称的简写：**合并、查询**。
> 具体而言，并查集支持以下操作：
> 1. 合并两个集合；
> 2. 查询两个元素是否在同一集合内。

它的代码只有几行，复杂度接近 $O(1)$，是**性价比最高的数据结构**。
但在 Python 里有一个必须绕开的坑：**递归版的 `find` 会爆栈**。

---

## 1　基本结构：森林

基本思路：

> 使用树可以很方便地表示并查集。类似于一堆的单向链表，
> 为每个元素记录一个父亲指针 `father` 就可以实现。
> 如果 `father` 为 `NULL`，说明该元素为树根，也就是这个集合的代表元素。

```text
function link(int x, int y):     // 保证 x 和 y 均为树根
    if x == y: return
    father[x] = y

function find(int x):
    while father[x] != NULL:
        x = father[x]
    return x
```

Python 里用 `fa[x] == x` 表示根（比 `None` 快，且省掉判空）：

```python
# 初值取 i 自己：开局每个元素独占一个集合，且「是不是根」统一判 fa[x] == x
# 长度取 n+1：题目编号多从 1 开始，多留第 0 格就能让 fa[i] 直接对应元素 i
fa = list(range(n + 1))          # fa[i] = i 表示 i 是根
```

**朴素版的问题**：链状结构下 `find` 是 $O(n)$，$q$ 次操作就是 $O(nq)$。
需要优化。

---

## 2　两种优化

### 优化一：路径压缩

> 由于只有合并操作，同一集合中的元素只增不减，
> 所以一棵树的形态其实**可以随意更改而没有任何副作用**。
> 路径压缩是一种偷懒的做法：合并的时候什么都不做，
> 而在 `find` 的时候将所有遍历到的元素的 `father` 全部改为根节点。

C++ 一行搞定：

```cpp
int find(int x) { return f[x] == x ? x : f[x] = find(f[x]); }
```

**但这在 Python 里是个陷阱**，见 §3。

### 优化二：按秩合并 / 按大小合并

> 按秩合并：记录每棵树的高度，每次合并时，**选取较高的树作为树根**。
> 采用按秩合并策略，树的高度为 $O(\log n)$。

还有一个省空间的技巧：

> 注意到只需要树根的 `rank` 值，而树根的 `father` 值为空。
> 为了充分利用空间，**树根的 `father` 可以存储 `-rank`**。

实战中更常用「按**大小**合并」（记录集合元素个数），因为很多题本来就要查集合大小。

### 复杂度对照

| 优化 | `find` 均摊复杂度 |
| --- | --- |
| 无 | $O(n)$ |
| 只按秩合并 | $O(\log n)$ |
| **只路径压缩** | **$O(\log n)$** 均摊 |
| **两者都用** | **$O(\alpha(n))$** |

$\alpha$ 是 Ackermann 反函数：

> 当 $n \le 10^{80}$ 时 $\alpha(n) \le 3$。**基本上可以认为是 $O(1)$ 了。**

还有一句非常实用的经验：

> 目前 98% 的 OI 代码里面的并查集，都只用了路径压缩优化……
> 因为大部分数据是随机的，只用路径压缩，树高就已经被压到常数级。
> **结论：不出意外，只写路径压缩就够了。并查集只有两行代码。**

> **但在 Python 里两个都值得写。** 理由不是理论复杂度，而是常数：
> 按大小合并能让路径变浅，从而**减少 `find` 内层 while 循环的 Python 层迭代次数**。
> 每少一次迭代就是实打实的时间，而多写的代码只有三行。

---

## 3　Python 的关键取舍：`find` 必须写成迭代

```python
# ❌ 直译 C++ 的递归版
def find(x):
    if fa[x] != x:                           # 不是根就继续往上找
        # 回溯时顺手把父指针改成根，这就是路径压缩；
        # 代价是递归深度等于当前树高，压缩生效前树高可达 n
        fa[x] = find(fa[x])
    return fa[x]
```

三个问题：

| 问题 | 后果 |
| --- | --- |
| **递归深度** | 未压缩前链长可达 $n$。$n = 5\times10^5$ 时**必然爆栈** |
| `sys.setrecursionlimit` 救不了 | 它只改计数器，C 栈仍会溢出 → **段错误，无报错** |
| 函数调用开销 | 每层递归约 0.1 μs，比迭代慢 3–5 倍 |

**正确写法：两趟迭代**。

```python
def find(x):
    """迭代式路径压缩。第一趟找根，第二趟把路径上所有点直接挂到根下。"""
    # 第一趟：顺着父指针走到底，fa[root] == root 的那个点就是集合代表元
    root = x
    while fa[root] != root:
        root = fa[root]
    # 第二趟：从 x 再走一遍，沿途每个点直接改指向 root，这条链被彻底压平
    # 条件写 fa[x] != root 而不是 x != root，已经挂在根下的点无需再动
    while fa[x] != root:                     # 第二趟压缩
        fa[x], x = root, fa[x]               # 先记下原父亲再改
    return root
```

> `fa[x], x = root, fa[x]` 这一行是关键：
> 右边先整体求值成元组（用的是**旧的** `fa[x]`），再解包赋值，
> 所以能在一行内完成「改父亲」和「走到原父亲」两件事。
> 见 [运算符与位运算](../python/operators.md)。

### 更快的写法：路径减半（path halving）

只用**一趟**循环，每走两步就把当前节点挂到祖父上：

```python
def find(x):
    """路径减半：一趟循环，边找根边压缩。理论复杂度同路径压缩，常数更小。"""
    while fa[x] != x:
        fa[x] = fa[fa[x]]                    # 挂到祖父，这条链的长度当场减半
        x = fa[x]                            # 跳到刚设好的新父亲，一次上升两级
    return x
```

| 写法 | 循环趟数 | 压缩效果 | Python 实测 |
| --- | --- | --- | --- |
| 递归压缩 | — | 完全压平 | ❌ 会爆栈 |
| 两趟迭代 | 2 | 完全压平 | 1× |
| **路径减半** | **1** | 树高减半 | **约 1.3× 快** |

$n, q$ 上到 $5\times10^5$ 时，**路径减半是首选**。

---

## 4　模板一：标准并查集类

```python
# DSU 是 Disjoint Set Union（不相交集合的合并）的缩写，即并查集
class DSU:
    """并查集：路径减半 + 按大小合并。均摊 O(alpha(n))，兼容 Python 3.9。

    元素编号 0..n-1（用 1..n 时把 n 传成 n+1 即可）。
    """

    __slots__ = ("fa", "sz", "cnt")          # 固定属性表：省掉实例字典，取属性更快

    def __init__(self, n):
        # fa[i] = i 表示 i 自成一个集合，同时兼作「i 是根」的标记
        self.fa = list(range(n))
        self.sz = [1] * n                    # 只有根上的 sz 有效，记该集合的元素个数
        self.cnt = n                         # 当前集合个数

    def find(self, x):
        fa = self.fa                         # 绑成局部名，循环里比每次取属性快
        while fa[x] != x:                    # 走到 fa[x] == x，即到达根
            fa[x] = fa[fa[x]]                # 路径减半
            x = fa[x]
        return x

    def union(self, x, y):
        """合并，返回是否真的发生了合并。"""
        x = self.find(x)                     # 合并只在两个根之间进行
        y = self.find(y)
        if x == y:
            return False                     # 已同集合：结构不动，集合数也不减
        if self.sz[x] < self.sz[y]:          # 按大小合并：小的挂到大的下面
            x, y = y, x                      # 交换后 x 恒为较大集合的根
        self.fa[y] = x                       # 小集合整体挂过去，树高增长最慢
        self.sz[x] += self.sz[y]             # 大小只在新根上累加，sz[y] 从此作废
        self.cnt -= 1                        # 两个集合并成一个
        return True

    def same(self, x, y):
        return self.find(x) == self.find(y)  # 同集合等价于代表元相同

    def size(self, x):
        return self.sz[self.find(x)]         # 必须先找根，sz 只有根上的值可信
```

### 模板二：扁平数组版（**大规模题的必需品**）

$n, q \ge 5\times10^5$ 时，方法调用（`self.find(x)`）的开销会成为瓶颈：
每次调用要建栈帧、查 `self.fa` 属性。**把 `find` 内联进主循环**能快 2 倍以上。

```python
import sys


def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); q = int(data[1])
    fa = list(range(n + 1))                  # 编号 1..n，第 0 格空着换取下标直接对应
    sz = [1] * (n + 1)
    p = 2                                    # token 游标：n 和 q 两个已经消费掉
    out = []
    for _ in range(q):
        op = data[p]; p += 1
        # split() 切出来的是 bytes，比较对象必须写成 b"1" 而不是 "1"
        if op == b"1":
            x = int(data[p]); y = int(data[p + 1]); p += 2
            # ---- 内联 find(x) ----
            while fa[x] != x:
                fa[x] = fa[fa[x]]            # 路径减半，循环结束时 x 已是根
                x = fa[x]
            # ---- 内联 find(y) ----
            while fa[y] != y:
                fa[y] = fa[fa[y]]
                y = fa[y]
            if x != y:                       # 两个根不同才需要真的合并
                if sz[x] < sz[y]:            # 按大小合并，保证 x 是较大集合的根
                    x, y = y, x
                fa[y] = x
                sz[x] += sz[y]
        ...
```

丑，但快。**只在被卡常时才这么写**。

---

## 5　带权并查集

在 `fa` 之外再维护一个 `w[x]`，表示 **$x$ 到其父节点的某种「距离」**。
路径压缩时需要把权值一路累积上去。

用途：维护「元素之间的相对关系」，比如：

- $x$ 和 $y$ 相差多少（差分约束的离线版）；
- $x$ 和 $y$ 的奇偶性关系；
- 食物链问题（三种关系循环）。

```python
class WeightedDSU:
    """带权并查集：w[x] 表示 x 相对于其父节点的偏移量（可换成模 k 的关系）。

    find 采用「两趟迭代」，因为权值必须自顶向下累积，路径减半会算错。
    """

    __slots__ = ("fa", "w")

    def __init__(self, n):
        self.fa = list(range(n))
        # 初值 0：此时人人都是自己的根，到父节点的偏移量自然为 0
        self.w = [0] * n                     # w[x] = val(x) - val(fa[x])

    def find(self, x):
        fa, w = self.fa, self.w
        root = x
        while fa[root] != root:              # 第一趟：找根
            root = fa[root]
        # 第二趟：一边压缩一边累积权值
        acc = 0
        cur = x
        # 先把 x 到根之间的中间节点按「从下往上」的顺序收集起来
        path = []
        while fa[cur] != root and fa[cur] != cur:
            path.append(cur)
            cur = fa[cur]
        # cur 的父亲已是 root（或 cur 就是 root）
        # 倒着遍历即「从靠近根的一端往下」：更新 node 时它父亲的 w 已经
        # 是相对根的值，w[node] 加上去才是 node 到根的偏移
        for node in reversed(path):
            w[node] += w[fa[node]]           # 先累积权值，此刻读到的还是旧父亲
            fa[node] = root                  # 再改指针，顺序颠倒会丢掉中间那段偏移
        return root

    def union(self, x, y, d):
        """声明 val(y) - val(x) = d。返回是否与已有约束相容（False 表示矛盾）。"""
        # 先 find：w[x]、w[y] 只有在压缩到根之后才是「相对根」的偏移
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            # 同根时两者的偏移之差已经确定，新约束只能核对不能修改
            return self.w[y] - self.w[x] == d      # 检查一致性
        self.fa[ry] = rx
        # 由 val(y) - val(x) = d 反解 ry 相对新父亲 rx 的偏移：
        # val(ry) - val(rx) = (val(y) - w[y]) - (val(x) - w[x]) = w[x] + d - w[y]
        self.w[ry] = self.w[x] + d - self.w[y]
        return True

    def diff(self, x, y):
        """返回 val(y) - val(x)，前提是两者在同一集合。"""
        self.find(x); self.find(y)           # 两边都压到根，w 才在同一基准上
        return self.w[y] - self.w[x]
```

> **带权并查集的核心易错点**：路径压缩时权值必须**从根往下**累加，
> 所以**不能用路径减半**（它是自底向上跳的，会把权值算重）。
> 必须先把路径存下来，再从靠近根的一端开始更新。

---

## 6　扩展域并查集（种类并查集）

当关系不止「同类」，还有「敌对」时，把每个元素**拆成多个域**：

| 问题 | 域的设计 |
| --- | --- |
| 「我朋友的朋友是我朋友，敌人的敌人是朋友」 | $x$ 和 $x+n$（朋友域、敌人域） |
| 食物链（A 吃 B，B 吃 C，C 吃 A） | $x$、$x+n$、$x+2n$（同类、猎物、天敌） |
| 二分图判定 | $x$ 和 $x+n$（两侧） |

```python
# 「敌人的敌人是朋友」的标准写法
# 每个元素拆成两个域：编号 x 代表「与 x 同阵营」，x + n 代表「与 x 敌对」
# 偏移量就是「第几个域乘以 n」，食物链那类三种关系再加一个 x + 2n 域
d = DSU(2 * n)

def set_friend(x, y):
    d.union(x, y)              # 同阵营域并到一起
    d.union(x + n, y + n)      # 敌对域同步合并，否则「共同的敌人」传不下去

def set_enemy(x, y):
    d.union(x, y + n)          # x 的朋友域 与 y 的敌人域 合并
    d.union(x + n, y)          # 对称的另一半，两次合并缺一不可

def is_friend(x, y):
    return d.same(x, y)        # 落在同一个朋友域即同阵营

def contradiction(x, y):
    return d.same(x, y) and d.same(x, y + n)     # 既是朋友又是敌人 -> 矛盾
```

「程序自动分析」的经典模板就是这个模型的简化版
（先处理全部「相等」约束，再检查所有「不等」约束是否被违反）：

```cpp
for (i = 1; i <= n; i++) {
    scanf("%d%d%d", &x, &y, &z);
    if (z == 1) { if (find(x) != find(y)) f[find(x)] = find(y); }
    else { a[temp] = x; b[temp++] = y; }        // 不等约束先存下来
}
// 全部合并完之后，再逐条检查不等约束
if (find(a[i]) == find(b[i])) p = false;
```

> **这个「先处理所有等式，最后统一检查不等式」的套路很通用**：
> 因为并查集不支持「拆分」，所以**必须把所有合并操作排在所有查询之前**。
> 遇到「有等式也有不等式」的题，第一反应就是分两趟。

---

## 7　并查集的经典套路

| 套路 | 说明 |
| --- | --- |
| 连通性判定 | 最基本用法 |
| **Kruskal 最小生成树** | 按边权排序 + 依次合并（[最小生成树](../graph/mst.md)） |
| 「最早何时全部连通」 | 排序 + 合并，`cnt == 1` 时即答案（BISHI104） |
| **离线倒序处理删除** | 删边/删点 → 倒过来变成加边/加点 |
| 二分图判定 | 扩展域，或染色 BFS |
| 维护相对关系 | 带权并查集 |
| 区间合并 / 「找下一个未使用的位置」 | `fa[i]` 指向 $i$ 右边第一个可用位置 |

### 「找下一个可用位置」的技巧

这是并查集一个非常巧妙的非典型用法：

```python
# 长度取 n+2：最后一格被占用后指针会指向 n+1，多留的这一格是越界哨兵
fa = list(range(n + 2))          # fa[i] = i 右边第一个还没被占用的位置

def find(x):
    # 和普通并查集同构：这里的「根」就是从 x 往右数第一个空位
    while fa[x] != x:
        fa[x] = fa[fa[x]]        # 路径减半，让后续查询少跳几格
        x = fa[x]
    return x

def occupy(x):
    """占用位置 x，之后 find(x) 会自动跳到下一个空位。"""
    p = find(x)                  # p 是 x 及其右侧第一个可用位置
    fa[p] = p + 1                # 占掉 p 后把它指向右邻居，以后查询自动跳过
    return p
```

把「线性扫描找空位」的 $O(n)$ 降到均摊 $O(\alpha)$。
「区间赋值只做一次」「每个格子只被填一次」类的题都能用它加速。

---

## 8　例题

<!-- CHAPTER-EXAMPLE-TABLE -->

### BISHI102 【模板】并查集（较难）

> $n, q \le 5\times10^5$。三种操作：
> `1 i j` 合并 $i$、$j$ 所在集合；
> `2 i j` 查询是否同集合，输出 `YES`/`NO`；
> `3 i` 输出 $i$ 所在集合的元素数量。
> 时限：C/C++ 5 秒，**其他语言 10 秒**；空间 C/C++ 512M，其他语言 1024M。
> 题面见 [原题](https://www.nowcoder.com/practice/513111e4477c4fad8f19f14d4cdf49dc)。


算法零难度，**全部难点在 $5\times10^5$ 规模下的 Python 常数**。
出题人把「其他语言」时限开到 10 秒，说明他知道这题对慢语言不友好。

工程要点，一条都不能少：

| 要点 | 理由 |
| --- | --- |
| `sys.stdin.buffer.read().split()` 一次读完 | $10^6$ 次 `input()` 光系统调用就超时 |
| `find` 用**路径减半**，不用递归 | 递归必爆栈；减半比两趟快 30% |
| **把 `find` 内联进主循环** | 省掉 $10^6$ 次函数调用 |
| 按大小合并 | 让 `while` 循环的迭代次数更少 |
| `fa`、`sz` 绑成局部名 | `LOAD_FAST` 比 `LOAD_GLOBAL` 快 |
| 输出攒进 list 最后 `join` | 省掉 $5\times10^5$ 次 `print` |

```python
import sys


def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); q = int(data[1])
    # fa[i] = i 即「i 自成一个集合」，同时兼作根标记；开 n+1 格让下标直接对应编号
    fa = list(range(n + 1))
    # sz 只有根上的值有意义，初值 1 表示每个集合起初只有自己一个元素
    sz = [1] * (n + 1)
    # token 游标：n 和 q 已经消费掉，从第 3 个 token 开始是操作
    p = 2
    out = []
    push = out.append
    for _ in range(q):
        op = data[p]; p += 1
        # split() 得到的是 bytes，比较对象必须写成 b"1" 而非 "1"
        if op == b"1":                       # 合并
            x = int(data[p]); y = int(data[p + 1]); p += 2
            # 内联的路径减半 find：循环结束时 x 已经被换成所在集合的根
            while fa[x] != x:
                fa[x] = fa[fa[x]]
                x = fa[x]
            while fa[y] != y:
                fa[y] = fa[fa[y]]
                y = fa[y]
            # 根不同才需要真的合并；根相同说明本来就在同一集合，什么都不用做
            if x != y:
                # 按大小合并：交换后 x 恒为较大集合的根，小的挂到大的下面，树最浅
                if sz[x] < sz[y]:
                    x, y = y, x
                fa[y] = x
                # 大小只在新根上累加，sz[y] 从此作废
                sz[x] += sz[y]
        elif op == b"2":                     # 查询同集合
            x = int(data[p]); y = int(data[p + 1]); p += 2
            # 同集合的判据是代表元相同，所以两边都要先压到根
            while fa[x] != x:
                fa[x] = fa[fa[x]]
                x = fa[x]
            while fa[y] != y:
                fa[y] = fa[fa[y]]
                y = fa[y]
            push("YES" if x == y else "NO")
        else:                                # 3：集合大小
            # 操作 3 只吃一个参数，游标只前进 1 格
            x = int(data[p]); p += 1
            while fa[x] != x:
                fa[x] = fa[fa[x]]
                x = fa[x]
            # 取到根之后再读 sz，非根位置上的 sz 是过期数据
            push(str(sz[x]))
    sys.stdout.write("\n".join(out) + "\n")


main()
```

**读格式的坑**：操作 3 只有**两个 token**（`3 i`），操作 1、2 有**三个**。
行长度不固定，**必须用游标按 token 读**，不能按行数组切片。

**空间估算**：`fa` 和 `sz` 各是 $5\times10^5$ 个小整数的 `list`，
指针数组约 4MB，加上被引用的小整数对象（$\le 256$ 的有缓存，更大的每个 28 字节），
最坏约 30MB。`data` 的 token 列表最大约 $1.5\times10^6$ 个 `bytes`，约 60MB。
总计远低于 1024MB 限制。

> **Python 现实性判断**：$q = 5\times10^5$，每次操作约 5–15 次 Python 层循环迭代
> （路径减半后树高稳定在 2–3），主循环总量约 $5\times10^6$ 次。
> 在 10 秒限制下**应该能过，但没有太多余量**。
> 三个分支的 `find` 已经全部展开成重复代码；若仍然 TLE，
> 剩下的手段是去掉 `sz`，改用「按索引小的当根」这一启发式。

题解：[`solutions/nowcoder/BISHI102/sol.py`](../solutions/BISHI102.md)（已通过判题机验证）
### BISHI104 修复公路（中等）

> $N \le 10^3$ 个城市、$M \le 10^5$ 条双向公路，第 $i$ 条连接 $x_i, y_i$ 且在第 $t_i$ 秒修完。
> 问**最早何时任意两个城市都能通车**；若全部修完仍不连通则输出 $-1$。
> 题面见 [原题](https://www.nowcoder.com/practice/8111efc8c04d472da349b6e5010e1951)。


**这是并查集最经典的应用形态**，也是 Kruskal 算法的骨架：

1. 把所有边按修完时间 $t$ **升序**排序；
2. 依次合并，每成功合并一次，连通块数减 1；
3. 连通块数变成 1 的那一刻，**当前这条边的 $t$ 就是答案**；
4. 全部处理完仍不为 1，输出 $-1$。

```python
import sys


def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); m = int(data[1])
    edges = []
    p = 2
    for _ in range(m):
        x = int(data[p]); y = int(data[p + 1]); t = int(data[p + 2]); p += 3
        edges.append((t, x, y))
    edges.sort()                             # 按时间升序 —— 元组比较，第一维就是 t
    # fa[i] = i：每座城市起初各自为一个连通块
    fa = list(range(n + 1))
    cnt = n                                  # 当前连通块数
    ans = 0 if n == 1 else -1                # ★ n=1 时本来就连通，答案是 0
    for t, x, y in edges:
        # 内联的路径减半 find，循环结束时 x、y 各自变成所在连通块的根
        while fa[x] != x:
            fa[x] = fa[fa[x]]
            x = fa[x]
        while fa[y] != y:
            fa[y] = fa[fa[y]]
            y = fa[y]
        # 两个根不同才是「这条路真的接通了两个块」，重复边不能让 cnt 减多
        if x != y:
            fa[y] = x
            cnt -= 1
            if cnt == 1:                     # 刚好全连通
                # 边已按时间升序，第一次连通时的 t 就是最早时刻
                ans = t
                break
    sys.stdout.write(str(ans) + "\n")


main()
```

复杂度 $O(M \log M)$（瓶颈是排序，C 层 Timsort）。$M = 10^5$ 稳过。

**三个坑**：

1. **$N = 1$ 时答案是 0**（一个城市自然连通，不需要任何公路）。
   如果只写 `ans = -1`，`cnt` 初始就是 1，循环里永远触发不了 `cnt == 1`，
   会错误地输出 $-1$。上面代码里 `ans = 0 if n == 1 else -1` 那一行就是在补这个洞——
   **这类「规模为 1」的退化情况是模板题最常见的隐藏用例**；
2. 找到答案后要 **`break`**，否则会被后面的边覆盖（虽然 `ans` 不会再被赋值，但白跑）；
3. 排序要按 $t$ **升序**，写成 `edges.sort(key=lambda e: e[0])` 也对，
   但直接把 $t$ 放元组第一维再 `sort()` 更快（省掉 $10^5$ 次 lambda 调用）。

> **和最小生成树的关系**：这题就是 Kruskal 求最小瓶颈生成树——
> 答案是 MST 中的**最大边权**。所以也可以直接跑完整的 Kruskal 取最大边。
> 见 [最小生成树](../graph/mst.md)。

题解：[`solutions/nowcoder/BISHI104/sol.py`](../solutions/BISHI104.md)（已通过判题机验证）
### BISHI98 谍中谍中谍中谍中谍…（中等）

> $n \le 1000$ 名学生，每人 $i$ 指认一个 $p_i$，构成**每点出度为 1 的有向图**。
> 从任意起点 $a$ 出发沿指认关系走，**第一次遇到已被警告过的学生**时该生退学。
> 对每个起点 $a$，输出最终退学的学生编号。
> 题面见 [原题](https://www.nowcoder.com/practice/ee1246384c9b4066b67043ebb37fd9c9)。


**这是「函数图（functional graph）」模型**：每个点出度为 1，
所以从任意点出发的路径一定是「一条尾巴 + 一个环」的 $\rho$ 形。

**关键观察**：第一个被重复访问的点，就是**路径上遇到的第一个环上节点**（环的入口）。

$n \le 1000$，$O(n^2)$ 暴力（每个起点独立走一遍，最多走 $2n$ 步）只有 $2\times10^6$，
在 Python 里也就 1 秒左右，时限「其他语言 2 秒」——能过但不宽裕。
$O(n)$ 的写法更稳：

```python
import sys


def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    # 前面补一个 0：学生编号从 1 起，让 p[i] 直接是 i 指认的人
    p = [0] + [int(v) for v in data[1:1 + n]]
    ans = [0] * (n + 1)
    # color: 0 未访问, 1 在当前这条路径上, 2 已确定答案
    color = [0] * (n + 1)
    for s in range(1, n + 1):
        # 已染色的点答案早就算好，跳过它才能保证总步数是 O(n)
        if color[s]:
            continue
        # path 按访问顺序记录本次走过的点，回填答案时要倒着用
        path = []
        u = s
        while color[u] == 0:                 # 一直走到「已在本路径上」或「已确定」
            color[u] = 1
            path.append(u)
            u = p[u]
        if color[u] == 1:                    # 撞上本次路径 -> 找到一个新环，u 是环入口
            entry = u
            # 环上所有点的答案都是它自己
            # 从 path 末尾往回退，退到 entry 为止，这一段正好是环
            k = len(path) - 1
            while path[k] != entry:
                ans[path[k]] = path[k]
                color[path[k]] = 2
                k -= 1
            ans[entry] = entry
            color[entry] = 2
            # 尾巴上的点，答案继承后继
            # k 停在 entry 处，所以尾巴是 path[0..k-1]，倒序保证后继已算好
            for j in range(k - 1, -1, -1):
                ans[path[j]] = ans[p[path[j]]]
                color[path[j]] = 2
        else:                                # color[u] == 2，接到已算好的部分
            # 整条路径都是尾巴，逐点继承后继的答案
            for j in range(len(path) - 1, -1, -1):
                ans[path[j]] = ans[p[path[j]]]
                color[path[j]] = 2
    sys.stdout.write(" ".join(map(str, ans[1:])) + "\n")


main()
```

**验证样例**（`n=3, p = 2 3 1`）：三个点构成一个环 $1\to2\to3\to1$，
每个点自己就是环入口，答案 `1 2 3` ✓（题面样例输出正是 `1 2 3`）。

**并查集在这题的角色**：也可以用「边加边合并，发现自环即找到环」的方式做，
但函数图的染色法更直接。**并查集不擅长有向图**——它维护的是无向连通性，
不区分方向。看到「有向」两个字要先想清楚并查集是否适用。

> **本题的关键坑**：`color == 1`（在本次路径上）和 `color == 2`（已定答案）
> 必须分开。只用一个 `visited` 标记会分不清「撞到新环」和「接到旧结果」，
> 这是函数图找环最常见的 bug。

### 大纲中另外两道题的说明

大纲把 **BISHI99「我朋友的朋友不是我的朋友」** 和 **BISHI101「世界树上找米库」**
也列在本章，但它们的实际考点并不是并查集：

| 题 | 实际考点 | 建议讲解位置 |
| --- | --- | --- |
| BISHI99 | 统计每个点的度数，判定 $\deg(x)^2 > \sum_{y \in N(x)} \deg(y)$；需要「字符串 → 编号」的映射 | [哈希表](hash.md) / [图的表示与遍历](../graph/basic.md) |
| BISHI101 | 从所有叶子出发的**多源 BFS**，求「到最近叶子距离最大」的非叶节点 | [BFS广度优先搜索](../search/bfs.md) / [树的基础与遍历](../graph/tree/basic.md) |

BISHI99 里 $\operatorname{avg}(x) = \frac{\sum_{y \in N(x)} \deg(y)}{\deg(x)}$，
判定 $\deg(x) > \operatorname{avg}(x)$ 时**两边同乘 $\deg(x)$ 变成整数比较**，
避免浮点误差——这是个通用技巧，见
[浮点与科学计数法](../toolkit/float.md)。

---

题解：[`solutions/nowcoder/BISHI98/sol.py`](../solutions/BISHI98.md)（已通过判题机验证）

## 9　本章速查

| 要点 | 结论 |
| --- | --- |
| 数据结构 | `fa` 数组，`fa[x] == x` 表示根 |
| **Python 的 `find`** | **必须迭代**，递归会爆 C 栈（无报错的段错误） |
| 最快写法 | **路径减半**：`fa[x] = fa[fa[x]]; x = fa[x]` |
| 完全压平写法 | 两趟迭代（带权并查集必须用这个） |
| 合并策略 | 按大小 / 按秩，让树更浅 |
| 复杂度 | 压缩 + 按秩 = 均摊 $O(\alpha(n))$，$\alpha \le 3$ |
| 只写路径压缩 | 均摊 $O(\log n)$，实战够用 |
| $n \ge 5\times10^5$ | **把 `find` 内联进主循环**，省函数调用 |
| 不支持的操作 | **删除、拆分**（所以有删除就离线倒序处理） |
| 有向图 | 并查集**不区分方向**，慎用 |
| 等式 + 不等式 | **先合并所有等式，再统一检查不等式** |
| 「最早何时全连通」 | 按时间排序 + 合并，`cnt == 1` 时即答案 |
| 「找下一个空位」 | `fa[i]` 指向 $i$ 右边第一个可用位置 |
| 带权并查集 | 权值自顶向下累积，**不能用路径减半** |
| 扩展域 | $x$ / $x+n$ / $x+2n$ 表示不同「域」 |

| 看到什么 → 想到并查集 |
| --- |
| 连通性、「是否在同一组」 |
| 最小生成树、最小瓶颈路 |
| 「最早/最晚何时连通」 |
| 「依次删边/删点」→ 倒序变加边 |
| 「敌人的敌人是朋友」→ 扩展域 |
| 「$a$ 比 $b$ 大 $d$」类相对关系 → 带权 |
| 「每个位置只能用一次，找下一个空位」 |

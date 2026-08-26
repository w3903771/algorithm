---
id: ds/segment-tree
title: 线段树
volume: 2
lang: py
---

# 第 39A 章　线段树

<!-- CHAPTER-EXAMPLES -->
> **前置**：[树状数组](fenwick.md)

线段树把序列切成一棵二叉的区间树，于是「区间改 + 区间查」这类操作都能在
$O(\log n)$ 内完成。它比[树状数组](fenwick.md)强的地方只有一条，但很关键：
**不要求信息可减**——最值、区间赋值、多重懒标记都能维护。

代价是常数。在 Python 里线段树的瓶颈**不是递归深度，而是函数调用次数**，
所以本章的模板一律是非递归的：把递归展开成「自顶向下 push + 自底向上 pull」两个循环。
选型决策表（哪种情况该用哪种结构）在 [数据结构目录页](index.md)。

---

## 1　结构

> 线段树实际上是**分治的产物**：将当前序列切为两半，分别递归下去处理。
> 除了叶节点，线段树上其余节点都表示一个区间。
> **对于任意一个区间，都可以被拆分成线段树上 $O(\log n)$ 个节点。**

性质：

| 性质 | 值 |
| --- | --- |
| 树高 | $\lceil \log n \rceil$ |
| 节点数 | $< 4n$（所以数组要开 $4n$） |
| 单次区间操作访问的节点数 | 最多 $4\lceil \log n \rceil$ |

常见的实现有两种：标准的递归实现，以及「标记永久化」的简化版
（只支持区间加、单点查）。

### 递归实现（教学版）

```python
import sys


class SegTreeRec:
    """递归线段树：区间加 + 区间和。教学用，理解懒标记的最佳形式。

    ⚠️ Python 下的问题：
      1. 递归深度 = log n，n = 1e6 时才 20 层，深度本身没问题；
      2. 但每次操作要 4*log n ≈ 80 次**函数调用**，
         n = q = 1e5 时就是 8e6 次调用，约 8-15 秒 —— 这才是致命的。
    实战请用 39.6 的非递归版本，或者干脆换树状数组。
    """

    def __init__(self, a):
        n = len(a)
        self.n = n
        self.sum = [0] * (4 * n)             # 节点数上界是 4n，见 39.5 的性质表
        self.tag = [0] * (4 * n)             # tag[p]：p 的儿子还欠着的区间加量
        self._build(1, 0, n - 1, a)          # 根编号 1，管辖闭区间 [0, n-1]

    def _build(self, p, l, r, a):
        if l == r:                           # 叶子：只管一个位置
            self.sum[p] = a[l]
            return
        m = (l + r) >> 1                     # 右移一位即除以 2 下取整，比 // 略快
        self._build(p * 2, l, m, a)          # 左儿子 2p 管 [l, m]
        self._build(p * 2 + 1, m + 1, r, a)  # 右儿子 2p+1 管 [m+1, r]
        self.sum[p] = self.sum[p * 2] + self.sum[p * 2 + 1]      # pull up

    def _push(self, p, l, r):
        """标记下传。对应 S2 代码里的 push()。"""
        t = self.tag[p]
        if t:                                # 标记为 0 时下传是纯粹的浪费，先挡掉
            m = (l + r) >> 1
            self.sum[p * 2] += t * (m - l + 1)       # 每个儿子按各自长度补上欠账
            self.sum[p * 2 + 1] += t * (r - m)       # 右儿子长度是 r-m，不是 r-m+1
            self.tag[p * 2] += t                     # 儿子的 tag 也要累加：欠账继续往下欠
            self.tag[p * 2 + 1] += t
            self.tag[p] = 0                          # 清零，避免同一笔账下传两次

    def _add(self, p, l, r, ql, qr, v):
        if ql <= l and r <= qr:              # 完全覆盖 -> 打标记，不再往下
            self.sum[p] += v * (r - l + 1)   # 本节点的和立刻更新，儿子先欠着
            self.tag[p] += v
            return                           # 这个提前返回就是 O(log n) 的来源
        self._push(p, l, r)                  # 要往下走，先把欠儿子的账还清
        m = (l + r) >> 1
        if ql <= m:                          # 查询区间与左半有交
            self._add(p * 2, l, m, ql, qr, v)
        if qr > m:                           # 查询区间与右半有交
            self._add(p * 2 + 1, m + 1, r, ql, qr, v)
        self.sum[p] = self.sum[p * 2] + self.sum[p * 2 + 1]      # 回溯后 pull up

    def _query(self, p, l, r, ql, qr):
        if ql <= l and r <= qr:              # 完全覆盖：sum 已含本节点的 tag，可直接用
            return self.sum[p]
        self._push(p, l, r)                  # 往下读之前必须下传，否则读到脏数据
        m = (l + r) >> 1
        res = 0
        if ql <= m:
            res += self._query(p * 2, l, m, ql, qr)
        if qr > m:
            res += self._query(p * 2 + 1, m + 1, r, ql, qr)
        return res

    def range_add(self, l, r, v):
        self._add(1, 0, self.n - 1, l, r, v)         # 对外是闭区间 [l, r]

    def query(self, l, r):
        return self._query(1, 0, self.n - 1, l, r)
```

### 懒标记（lazy tag）的本质

> 对于区间修改，每个节点记录一个**整体增量 offset**，
> 表示这个节点管辖范围内的所有元素都要加上这个值，但**还没有真正下传给儿子**。
> 访问儿子之前必须先**标记下传**，并且记得下传完毕后要更新 `sum`。

三条铁律：

1. **完全覆盖就打标记返回**，不再往下递归（这是复杂度的来源）；
2. **要往下走之前必须 push down**；
3. **递归回来之后必须 pull up**（用儿子更新自己）。

> **懒标记最常见的三个 bug**：
> - 忘了 push down → 查询到脏数据；
> - `push` 里更新了 `sum` 却忘了给儿子的 `tag` 也累加；
> - 乘法标记和加法标记同时存在时**顺序搞反**（见 §3 的 BISHI128）。

### 递归深度

线段树的递归深度只有 $O(\log n)$（$n = 10^6$ 时约 20 层），
**远低于 Python 的默认限制 1000，不需要 `sys.setrecursionlimit`**。

> 这一点常被误解。线段树的问题**从来不是递归深度，而是函数调用次数**：
> 每次区间操作要 $4\log n$ 次调用，$q = 10^5$ 时是 $8\times10^6$ 次。
> CPython 一次函数调用约 0.5–1 μs，光调用开销就是 **4–8 秒**。
>
> 需要 `setrecursionlimit` 的是 **DFS**（[DFS 深度优先搜索](../search/dfs.md)），不是线段树。

---

## 2　模板：非递归懒标记线段树

把递归展开成「自顶向下 push + 自底向上 pull」的两个循环，
消灭全部函数调用，是 Python 下线段树唯一有希望的写法。

```python
class LazySeg:
    """非递归懒标记线段树：区间加 + 区间和。O(log n) per op。

    结构（AtCoder Library 风格）：
      - size 是 >= n 的最小 2 的幂，叶子在 [size, 2*size)；
      - d[k] 是节点 k 的区间和（**已包含** lz[k] 的效果）；
      - lz[k] 是待下传给儿子的加法标记；
      - 节点 k 管辖的长度 = size >> (k.bit_length() - 1)。

    兼容 Python 3.9。
    """

    __slots__ = ("n", "size", "log", "d", "lz")

    def __init__(self, a):
        n = len(a)
        self.n = n
        size = 1
        log = 0
        while size < n:                      # 补齐到不小于 n 的 2 的幂，树才是满二叉树
            size <<= 1
            log += 1                         # log 同时就是树高，即叶子到根的层数
        self.size = size
        self.log = log
        self.d = [0] * (2 * size)            # 1 号是根，叶子占 [size, 2*size)
        self.lz = [0] * size                 # 只有内部节点需要标记，长度 size 就够
        d = self.d
        for i in range(n):
            d[size + i] = a[i]               # 下标 i 对应叶子 size+i；尾部空叶子留 0
        for i in range(size - 1, 0, -1):     # 倒序遍历保证访问 i 时两个儿子已算好
            d[i] = d[2 * i] + d[2 * i + 1]

    def _apply(self, k, x):
        """给节点 k 整体加 x。"""
        # k.bit_length()-1 是 k 所在层数，size >> 层数 = 该节点管辖的叶子个数
        self.d[k] += x * (self.size >> (k.bit_length() - 1))
        if k < self.size:                    # 叶子没有儿子，不必留标记
            self.lz[k] += x

    def range_add(self, l, r, x):
        """a[l..r) 全部 += x（左闭右开），O(log n)。"""
        if l >= r:                           # 空区间直接返回，否则下面的循环会越界
            return
        size, log, d, lz = self.size, self.log, self.d, self.lz
        l += size                            # 数组下标 -> 叶子编号
        r += size
        # 自顶向下 push，保证边界节点的祖先没有残留标记
        for i in range(log, 0, -1):
            # (l >> i << i) != l 表示 l 不是 2^i 的倍数，即第 i 层祖先只被部分覆盖
            if ((l >> i) << i) != l:
                k = l >> i                   # l 的第 i 层祖先
                if lz[k]:
                    t = lz[k]
                    self._apply(2 * k, t)    # 欠账转给两个儿子
                    self._apply(2 * k + 1, t)
                    lz[k] = 0
            if ((r >> i) << i) != r:
                k = (r - 1) >> i             # 右端开区间，真正涉及的最后一个叶子是 r-1
                if lz[k]:
                    t = lz[k]
                    self._apply(2 * k, t)
                    self._apply(2 * k + 1, t)
                    lz[k] = 0
        l2, r2 = l, r                        # 存下叶子编号，pull 阶段还要沿同两条路回去
        while l < r:                         # 自底向上取出覆盖 [l, r) 的 O(log n) 个整节点
            if l & 1:                        # l 是右儿子，父亲会越过左边界，只能吃下 l 本身
                self._apply(l, x)
                l += 1
            if r & 1:                        # r 是右儿子，说明 r-1 这一整块在区间内
                r -= 1
                self._apply(r, x)
            l >>= 1                          # 上升一层，区间端点同步折半
            r >>= 1
        # 自底向上 pull
        l, r = l2, r2
        for i in range(1, log + 1):          # 只有两条边界路径上的祖先的和会变
            if ((l >> i) << i) != l:
                k = l >> i
                # d[k] 的定义是「已含 lz[k] 效果」，所以合并儿子后要把自己的标记补回去
                d[k] = d[2 * k] + d[2 * k + 1] + lz[k] * (size >> (k.bit_length() - 1))
            if ((r >> i) << i) != r:
                k = (r - 1) >> i
                d[k] = d[2 * k] + d[2 * k + 1] + lz[k] * (size >> (k.bit_length() - 1))

    def query(self, l, r):
        """返回 a[l] + ... + a[r-1]（左闭右开），O(log n)。"""
        if l >= r:
            return 0
        size, log, lz = self.size, self.log, self.lz
        l += size
        r += size
        for i in range(log, 0, -1):          # 只读也要先 push：祖先的标记尚未落到儿子上
            if ((l >> i) << i) != l:
                k = l >> i
                if lz[k]:
                    t = lz[k]
                    self._apply(2 * k, t)
                    self._apply(2 * k + 1, t)
                    lz[k] = 0
            if ((r >> i) << i) != r:
                k = (r - 1) >> i
                if lz[k]:
                    t = lz[k]
                    self._apply(2 * k, t)
                    self._apply(2 * k + 1, t)
                    lz[k] = 0
        res = 0
        d = self.d
        while l < r:                         # 与 range_add 同一套端点上升，改成累加
            if l & 1:
                res += d[l]
                l += 1
            if r & 1:
                r -= 1
                res += d[r]
            l >>= 1
            r >>= 1
        return res                           # 查询不改数据，无需 pull
```

> **即使写成非递归，Python 的线段树依然很慢**：
> 每次操作约 $6\log n \approx 120$ 次 Python 层循环迭代，
> $q = 10^5$ 就是 $1.2\times10^7$ 次。相比之下双树状数组只要 $4\times10^6$ 次。
>
> **所以判断顺序是**：能用树状数组 → 用树状数组；
> 只有当维护的信息**不满足可减性**（最值、区间赋值、复杂标记）时才写线段树。

> **不要求可减性**，正是线段树相对树状数组不可替代的地方——
> 最值、区间赋值、复杂标记都能维护。对照见
> [树状数组 · 可减性](fenwick.md#5-可减性树状数组能做什么不能做什么)。

---

## 3　例题

<!-- CHAPTER-EXAMPLE-TABLE -->

### BISHI126 【模板】动态区间和Ⅱ ‖ 区间修改 + 区间查询（较难）

> $n, q \le 5\times10^5$，$|a_i|, |x| \le 10^7$。
> `1 l r x` 区间加，`2 l r` 区间求和。
> 时限：C/C++ 5 秒，**其他语言 10 秒**。
> 题面见 [原题](https://www.nowcoder.com/practice/ef7a50cf0377447b9b435b0f95e48e70)。

题面自己给了提示：

> 我们可以使用线段树解决……您也可以尝试使用**区间扩展版的树状数组**解决本题，
> 其运行时的**常数更小**。

**在 Python 里这不是「也可以」，是「必须」。** 用双树状数组（39.3 形态三）。

```python
import sys


def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); q = int(data[1])
    N = n + 2                                # 多留两格：range_add 会写到下标 r+1 = n+1
    t1 = [0] * (N + 1)                       # 差分树，存 d[j]
    t2 = [0] * (N + 1)                       # 加权差分树，存 (j-1) * d[j]

    def range_add(l, r, v):
        # 内联展开四次树状数组更新
        i = l; w = v * (l - 1)               # 左端点：d[l] += v，权重取 l-1
        while i <= N:
            t1[i] += v; t2[i] += w; i += i & -i          # 两棵树同一条向后路线一起走
        i = r + 1; v2 = -v; w2 = v * r       # 右端点后一格抵消，权重取 (r+1)-1 = r
        while i <= N:
            t1[i] += v2; t2[i] -= w2; i += i & -i

    def pre(i):
        s1 = 0; s2 = 0; j = i
        while j > 0:
            s1 += t1[j]; s2 += t2[j]; j -= j & -j        # 同样合并成一个循环，迭代数减半
        return s1 * i - s2                   # 前缀和 = i * sum(d) - sum((j-1)*d)

    # 初始数组：把 a[i] 看成一次 range_add(i, i, a[i])
    a = data[2:2 + n]                        # 保持 bytes，用到哪个才转 int
    for i in range(1, n + 1):
        v = int(a[i - 1])                    # 树状数组用 1..n，源数组用 0..n-1，差一位
        if v:
            range_add(i, i, v)               # 跳过 0：省下 n 次全 0 的树上行走

    p = 2 + n                                # token 游标，指向第一条操作
    out = []
    push = out.append
    for _ in range(q):
        op = data[p]
        if op == b"1":                       # 区间加：本条操作占 4 个 token
            l = int(data[p + 1]); r = int(data[p + 2]); x = int(data[p + 3])
            p += 4
            range_add(l, r, x)
        else:                                # 区间求和：本条操作占 3 个 token
            l = int(data[p + 1]); r = int(data[p + 2])
            p += 3
            push(pre(r) - pre(l - 1))        # 前缀相减取区间，l-1 在 l=1 时为 0，循环不进入
    sys.stdout.write("\n".join(map(str, out)) + "\n")


main()
```

**Python 现实性判断**：

| 项 | Python 层循环迭代数 |
| --- | --- |
| 初始化（$n$ 次单点加 = 2 次树状数组走） | $5\times10^5 \times 2 \times 19 \approx 1.9\times10^7$ |
| $q$ 次修改（4 次树状数组走） | $5\times10^5 \times 4 \times 19 \approx 3.8\times10^7$ |
| $q$ 次查询（2 次双树走） | $5\times10^5 \times 2 \times 19 \approx 1.9\times10^7$ |

总量约 $6\times10^7$ 次 Python 层循环迭代。按 $10^7$ 次/秒估算是 **6 秒**，
加上读入和输出，**余量不宽裕，但这份写法在 Python 3 下实测通过**。

**能做的优化已经全部用上**：
把 `range_add` 和 `pre` 写成闭包（局部变量访问）、两棵树同一循环走、
初始化时跳过 $a_i = 0$、输出一次性 `join`。

> **对照**：同一题用 39.6 的非递归懒标记线段树，
> 每次操作约 $6\log n = 114$ 次迭代，$10^6$ 次操作就是 $1.1\times10^8$ ——**必然超时**。
> **这就是「能用树状数组就别用线段树」的实证。**

题解：[`solutions/nowcoder/BISHI126/sol.py`](../solutions/BISHI126.md)（已通过判题机验证，Python 3）

### BISHI127 区间根号与区间求和（中等）

> $n, q \le 10^5$，$0 \le a_i \le 10^7$。
> `1 l r` 把区间内每个元素变成 $\lfloor \sqrt{a_i} \rfloor$；`2 l r` 区间求和。
> 时限：C/C++ 1 秒，**其他语言 2 秒**。
> 题面见 [原题](https://www.nowcoder.com/practice/56547df6934f4048a80ec75838d60c8f)。

**关键观察（势能分析）**：开根是**收敛极快**的操作。

$$10^7 \to 3162 \to 56 \to 7 \to 2 \to 1 \to 1 \to \cdots$$

**任何数最多开根 6 次就变成 1（或 0），之后再开根不变。**

所以「区间开根」的总工作量是 $O(6n)$ 次单点修改，而不是 $O(qn)$。
关键是**如何跳过那些已经稳定（$\le 1$）的位置**——用**并查集**：
`nxt[i]` 指向 $i$ 右边第一个还没稳定的位置。

区间和这一侧**不要用树状数组，要用分块**——理由见代码后的实测对比。

```python
import sys
from math import isqrt

B = 320                                      # 块长，约 sqrt(n)


def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); q = int(data[1])
    a = [int(v) for v in data[2:2 + n]]      # 0 下标，块号 = i // B

    nb = (n + B - 1) // B                    # 向上取整得块数，末块可能不满
    bsum = [sum(a[k * B:(k + 1) * B]) for k in range(nb)]    # 切片越界会自动截断，末块安全

    # 并查集：nxt[i] = i 右边第一个 a 值 > 1 的位置
    nxt = list(range(n + 1))                 # 多开一格：下标 n 是哨兵，代表「右边没有了」
    for i in range(n):
        if a[i] <= 1:                        # 0 和 1 开根都是自身，一开始就算稳定
            nxt[i] = i + 1                   # 直接指向右邻，find 时会被一路压缩掉

    def find(x):
        while nxt[x] != x:                   # 自指的位置就是代表元，即第一个未稳定位置
            nxt[x] = nxt[nxt[x]]             # 路径减半：顺手把 x 挂到祖父上，均摊近 O(1)
            x = nxt[x]
        return x                             # 哨兵 n 永远自指，所以查询必定终止

    p = 2 + n                                # token 游标
    out = []
    push = out.append
    for _ in range(q):
        op = data[p]
        l = int(data[p + 1]) - 1             # 题面 1-indexed，这里统一转 0-indexed
        r = int(data[p + 2]) - 1
        p += 3
        if op == b"1":                       # 区间开根：只碰还没稳定的位置
            i = find(l)                      # l 自己若已稳定，直接跳到右边第一个活跃位
            while i <= r:                    # i 越过 r（含跳到哨兵 n）就结束
                old = a[i]
                new = isqrt(old)
                a[i] = new
                bsum[i // B] += new - old    # 单点改块和，O(1)
                if new <= 1:                 # 稳定了，从并查集里摘掉
                    nxt[i] = i + 1
                i = find(i + 1)              # 从右邻重新找活跃位，已稳定的一段被整体跳过
        else:                                # 区间求和
            kl = l // B
            kr = r // B
            if kl == kr:                     # 同块，直接扫这一段
                push(sum(a[l:r + 1]))        # 单独处理，否则下面的三段式会把中间算重
            else:                            # 左残块 + 中间整块 + 右残块
                push(sum(a[l:(kl + 1) * B])  # 左残块：l 到本块末尾
                     + sum(bsum[kl + 1:kr])  # 中间整块：直接取块和，不碰元素
                     + sum(a[kr * B:r + 1]))  # 右残块：本块开头到 r
    sys.stdout.write("\n".join(map(str, out)) + "\n")


main()
```

**为什么是分块而不是树状数组**：两者都能做「单点改 + 区间查」，
但**代价结构正好相反**：

| | 单点修改 | 区间查询 |
| --- | --- | --- |
| 树状数组 | $O(\log n) = 17$ 步 Python 循环 | $2\times17$ 步 |
| 分块 | **$O(1)$**（改 `a[i]` 和所属块和） | $O(\sqrt n)$，但整段由 C 层的 `sum` 完成 |

本题的修改次数（$\le 6n = 6\times10^5$）远多于查询次数（$10^5$），
所以要把成本压到**修改**那一侧。

> $n = q = 10^5$ 的最坏数据实测：树状数组版 0.56 秒，分块版 0.35 秒，
> 而**只有分块版能在判题机上通过**。
>
> 这里有两条经验：
> 1. **本地耗时要留 3–4 倍余量再对照时限**。判题机的机器通常比本机慢数倍，
>    「本地 0.5 秒 / 时限 2 秒」看着有 4 倍余量，实际可能刚好不够；
> 2. 选数据结构要看**这道题的操作配比**，而不是套用「区间和就上树状数组」。
>    本题改多查少，就该把成本压到修改那一侧。

**三个要点**：

1. **`math.isqrt` 而不是 `int(x ** 0.5)`**——后者对 $10^7$ 附近的数可能算错 1，
   见 [运算符与位运算](../python/operators.md)；
2. 题面 2026-01-21 更新后**去除了负数数据**（$a_i \ge 0$），
   否则开根还要讨论负数；
3. 判定「稳定」的条件是 $\le 1$（$0$ 和 $1$ 开根都是自己），不是 $= 1$；
4. 查询要分「同块」与「跨块」两种情形写。写成统一形式会在 `kl == kr` 时
   把中间那段算重。

> ⚠️ `math.isqrt` 是 Python 3.8 才加的，而**牛客的 PyPy3 比 3.8 老，没有这个函数**
> （实测 `from math import isqrt` 直接 `ImportError`）。
> 所以这题只能用 Python3 提交，不能退化到 PyPy3 去换速度。

> **这题是「势能分析 + 并查集跳跃」的经典组合**：
> 单次操作最坏 $O(n)$，但**总量有界**，于是均摊后能过。
> 同类模型还有「区间取模」「区间对某数取 min（吉司机线段树）」。

题解：[`solutions/nowcoder/BISHI127/sol.py`](../solutions/BISHI127.md)（已通过判题机验证）

### BISHI128 区间加乘与单点求值（中等）

> $n, q \le 10^5$。`1 l r x` 区间加 $x$；`2 l r x` 区间乘 $x$；
> `3 x` 输出 $a_x \bmod 998244353$。
> 时限：C/C++ 1 秒，**其他语言 2 秒**。
> 题面见 [原题](https://www.nowcoder.com/practice/7a1de22fa7a1456f8ba519f21de31c84)。

> ⚠️ 本节只给出**建模片段**而非完整实现，该片段未经官方样例验证。
> 完整实现见本节末尾的题解链接。

**双标记线段树的经典题**，但注意只需要**单点查询**，这给了优化空间。

标记是一个**仿射变换** $x \mapsto kx + b$。两个变换的复合：

$$(k_2, b_2) \circ (k_1, b_1) = (k_1 k_2,\ b_1 k_2 + b_2)$$

即「先做 1 再做 2」等价于 $x \mapsto k_2(k_1 x + b_1) + b_2$。

> **顺序绝对不能反。** 这是双标记线段树的头号 bug 来源。
> 检验方法：先加 1 再乘 2，$x=0$ 应得 2；先乘 2 再加 1，$x=0$ 应得 1。

**做法一：懒标记线段树**，节点存 $(k, b)$，单点查询时从根走到叶累积。
每次操作约 $6\log n \approx 100$ 次迭代，$10^5$ 次操作 $= 10^7$，
2 秒限制下**极险**。

**做法二（Python 推荐）：离线 + 时间轴仿射复合。**

注意到只有单点查询，可以换个维度思考：

- 把**下标**作为扫描轴，从 $1$ 扫到 $n$；
- 每个修改操作 $(l, r, k, b)$ 在 $i = l$ 时「激活」，在 $i = r+1$ 时「失效」；
- 维护一棵以**时间**（操作序号）为下标的线段树，
  每个叶子存该操作的仿射变换（未激活时为恒等 $(1,0)$）；
- 根节点存的就是**当前所有激活操作按时间顺序的复合**；
- 查询 $a_x$：把根的仿射变换作用在初始值 $a_x$ 上。

这样每个操作只做 **2 次单点修改**（激活 + 失效），每次 $O(\log q)$；
查询是 $O(1)$（直接读根）。总量 $2q\log q \approx 3.4\times10^6$，**快 3 倍**。

```python
# [片段] 只给出离线做法的读入与建模部分，完整实现见正文说明
import sys

MOD = 998244353


def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); q = int(data[1])
    a = [0] + [int(v) % MOD for v in data[2:2 + n]]      # 前置 0 让下标与题面的 1..n 对齐
    # 读入即取模：a[i] 可能是负数，Python 的 % 直接给出 [0, MOD) 内的结果

    # 先读全部操作
    ops = []                                 # 修改操作，每项是仿射变换 (l, r, k, b)
    queries = []                             # 查询，每项是 (下标 x, 此前已有多少个修改)
    p = 2 + n
    for _ in range(q):
        t = data[p]
        if t == b"3":                        # 查询：只占 2 个 token
            x = int(data[p + 1]); p += 2
            queries.append((x, len(ops)))    # len(ops) 记下时间戳，离线时据此定位版本
        elif t == b"1":                      # 区间加 x，即仿射 (k, b) = (1, x)
            l = int(data[p + 1]); r = int(data[p + 2]); x = int(data[p + 3]) % MOD
            p += 4
            ops.append((l, r, 1, x))
        else:                                # 区间乘 x，即仿射 (k, b) = (x, 0)
            l = int(data[p + 1]); r = int(data[p + 2]); x = int(data[p + 3]) % MOD
            p += 4
            ops.append((l, r, x, 0))
    ...
```

> 完整实现需要「按下标扫描 + 时间轴线段树」，代码约 80 行，
> 属于**离线技巧**的范畴，详见
> [CDQ 分治](../technique/cdq.md)。
>
> **这里给出的教学要点是**：当线段树在 Python 里跑不动时，
> **先问「这题能不能离线」**——把在线数据结构换成离线扫描，
> 常常能把 $O(q\log n)$ 的大常数换成 $O(q \log q)$ 的小常数。

**如果坚持在线做**，用 39.6 的非递归框架把 `_apply` 改成仿射复合即可：

```python
def _apply(self, k, mul, add):
    """节点 k 的所有元素做 x -> x * mul + add。"""
    self.b[k] = (self.b[k] * mul + add) % MOD          # 已有偏移先乘再加
    self.m[k] = self.m[k] * mul % MOD
    # 单点查询不需要维护区间和，所以不用乘区间长度
```

**三个坑**：

1. **复合顺序**：新标记作用在旧标记**之后**，所以 `b = b * mul + add`，
   不是 `b = (b + add) * mul`；
2. $a_i$ 和 $x$ 都可能是**负数**（$\ge -10^7$），要先 `% MOD` 化到 $[0, MOD)$。
   Python 的 `%` 对负数返回非负结果，这一点比 C++ 省心；
3. 输出的是 $a_x \bmod 998244353$，**不是原值**——最终结果一定要取模。

> ⚠️ **BISHI128 必须用 PyPy3 提交。** 非递归线段树每次操作约 $4\log n$ 个节点、
> $q = 10^5$ 时是 $10^7$ 级的纯 Python 层迭代，且懒标记的下推有前后依赖，
> **无法向量化到 C 层**——CPython 实测超时，PyPy3 的 JIT 一次通过。
> 提交语言登记在该题 `meta.json` 的 `langs.py.submitLang` 字段。

题解：[`solutions/nowcoder/BISHI128/sol.py`](../solutions/BISHI128.md)（已通过判题机验证，PyPy3）

### BISHI130 区间取反与区间数一（中等）

> $n, q \le 5\times10^5$，01 串。`1 l r` 区间取反；`2 l r` 查询区间内 1 的个数。
> 时限：C/C++ 2 秒，**其他语言 4 秒**。
> 题面见 [原题](https://www.nowcoder.com/practice/55d474a878a84f4b84dca4b177a8c45c)。

标准解法是**线段树 + 翻转懒标记**：节点维护 `cnt`（区间内 1 的个数），
翻转时 `cnt = len - cnt`，标记异或。

实现要用**自底向上的迭代式线段树**（zkw 风格），不能写递归：

- 叶子放在 $[N,\ N+n)$，$N$ 是不小于 $n$ 的 2 的幂；
- 改 / 查之前，先把**左右两条边界路径**上的懒标记下推；
- 然后从两端向中间合并，沿途对「恰好被完整覆盖」的节点打标记 / 取值；
- 改完再从两端**自底向上**重算祖先的 `cnt`。

```python
import sys


def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); q = int(data[1])
    s = data[2]                              # 01 串整体是一个 token，保持 bytes 不解码

    N = 1
    while N < n:                             # 补齐到不小于 n 的 2 的幂，树才是满二叉树
        N <<= 1
    H = N.bit_length()                       # 叶子编号的位宽，即树高加一
    tree = [0] * (2 * N)                     # 区间内 1 的个数
    ln = [0] * (2 * N)                       # 区间的**有效**长度（虚拟叶子为 0）
    lz = bytearray(2 * N)                    # 翻转懒标记
    for i in range(n):
        tree[N + i] = s[i] - 48              # b'0' 是 48
        ln[N + i] = 1                        # 真实叶子长度 1；补齐出来的尾部叶子保持 0
    for i in range(N - 1, 0, -1):            # 倒序保证访问 i 时两个儿子已算好
        i2 = i << 1
        tree[i] = tree[i2] + tree[i2 + 1]
        ln[i] = ln[i2] + ln[i2 + 1]          # 有效长度同样自底向上汇总

    p = 3                                    # token 游标：前三个是 n、q、01 串
    out = []
    push_out = out.append
    for _ in range(q):
        op = data[p]
        lo = int(data[p + 1]) - 1 + N        # 左闭
        hi = int(data[p + 2]) + N            # 右开
        p += 3

        for a in (lo, hi - 1):               # 下推两条边界路径上的懒标记
            for sft in range(H, 0, -1):      # 从最高层往下；sft = H 时落在下标 0，恒空转
                j = a >> sft                 # a 的第 sft 层祖先
                if lz[j]:
                    for c in (j << 1, (j << 1) | 1):     # 左右儿子 2j 与 2j+1
                        tree[c] = ln[c] - tree[c]        # 翻转即用有效长度减去 1 的个数
                        if c < N:                        # 叶子没有儿子，不必留标记
                            lz[c] ^= 1                   # 翻转标记可叠加，用异或而非累加
                    lz[j] = 0                            # 清零，避免同一笔账下传两次

        if op == b"1":                       # ---- 区间取反 ----
            a = lo
            b = hi
            while a < b:                     # 自底向上收集覆盖 [lo, hi) 的整节点
                if a & 1:                    # a 是右儿子，父亲会越过左边界，只能吃下 a
                    tree[a] = ln[a] - tree[a]
                    if a < N:
                        lz[a] ^= 1
                    a += 1
                if b & 1:                    # b 是右儿子，说明 b-1 这一整块在区间内
                    b -= 1
                    tree[b] = ln[b] - tree[b]
                    if b < N:
                        lz[b] ^= 1
                a >>= 1                      # 上升一层，两个端点同步折半
                b >>= 1
            for a in (lo, hi - 1):           # 自底向上重算祖先
                a >>= 1                      # 从边界叶子的父亲开始，叶子自己已经改好
                while a:                     # 一路走到根（a 变成 0 才停）
                    t = tree[a << 1] + tree[(a << 1) | 1]
                    tree[a] = ln[a] - t if lz[a] else t  # 自己还挂着标记，合并结果要再翻一次
                    a >>= 1
        else:                                # ---- 区间数一 ----
            res = 0
            a = lo
            b = hi
            while a < b:                     # 与取反同一套端点上升，改成累加计数
                if a & 1:
                    res += tree[a]           # tree 已含本节点标记的效果，可直接取
                    a += 1
                if b & 1:
                    b -= 1
                    res += tree[b]
                a >>= 1
                b >>= 1
            push_out(res)                    # 查询不改数据，无需重算祖先

    sys.stdout.write("\n".join(map(str, out)) + "\n")


main()
```

**补齐到 2 的幂时，超出 $n$ 的虚拟叶子长度必须置 0**（而不是 1）。
否则翻转会把这些不存在的位置也算成 1，区间计数直接偏大——
这是补齐式线段树最容易漏的一处。

同理，自底向上重算祖先时，**若该祖先自己还挂着懒标记，要把合并结果再翻一次**
（`ln[a] - t if lz[a] else t`）。漏了这一步，标记就被算丢了。

### 为什么这题不能用分块

这一章反复强调「分块能把散块操作压到 C 层，是 Python 的好选择」。
但**本题是个例外**，值得单独说清楚，因为它划出了那条经验的适用边界。

分块在这题上每次操作都是 $O(n/B + B)$ 的，而且两头都压不下去：

1. **整块翻转躲不掉逐块改计数**。翻转会改变每块的 1 的个数
   （`cnt[i:j] = [B - c for c in ...]`），
   **不像「区间加」那样能用一个偏移量惰性跳过**；
2. **散块计数是 $O(B)$ 而不是 $O(B/64)$**。`bin(x).count("1")` 要先构造一个
   $B$ 字符的字符串，位图省下来的字长优势在这一步又还回去了；
3. 于是加大 $B$ 能压低块数，却同比抬高散块成本，**两头堵死**——
   最优点仍是每次操作上千次元素操作，$q = 5\times10^5$ 时总量 $10^9$ 级别。

实测（$n = q = 5\times10^5$）：

| 写法 | 每次操作 | 结果 |
| --- | --- | --- |
| 分块 + 大整数位图（CPython） | $O(\sqrt n)$，约上千次元素操作 | TLE |
| 分块 + 大整数位图（**PyPy3**） | 同上 | **仍然 TLE** |
| 迭代式线段树（**PyPy3**） | 约 76 步 | **AC** |

**第二行是关键**：换成 PyPy 也救不回分块。
$\sqrt{5\times10^5} \approx 707$ 而 $\log_2(5\times10^5) \approx 19$，两者差 37 倍，
**语言层的加速换不来渐进复杂度的差距**。

所以本章「优先分块」的经验要补一个前提：**分块的 $O(\sqrt n)$ 必须自己扛得住**。
$n, q \le 10^5$ 时 $\sqrt n \approx 316$，分块很划算；
到了 $5\times10^5$，$\sqrt n$ 已经涨到 707 而 $\log n$ 才 19，
这时候该回头写线段树——哪怕它每一步都在 Python 层。
BISHI138 是同一条原则在 DP 上的另一面。

> ⚠️ **BISHI130 必须用 PyPy3 提交。** 换成线段树后总量降到 $3.8\times10^7$ 次
> 纯 Python 层迭代，但全是带分支的指针跳转（懒标记下推、自底向上重算），
> **没有任何办法向量化到 C 层**，CPython 仍然超时。
> PyPy3 的 JIT 能把这种紧循环编译成机器码。
> 提交语言登记在该题 `meta.json` 的 `langs.py.submitLang` 字段。

题解：[`solutions/nowcoder/BISHI130/sol.py`](../solutions/BISHI130.md)（已通过判题机验证，PyPy3）
---

---

## 4　本章速查

| 要点 | 结论 |
| --- | --- |
| 节点数 | 开 $4n$ |
| 单次区间操作访问节点数 | $\le 4\lceil\log n\rceil$ |
| 递归深度 | 只有 $\log n$，**不需要 `setrecursionlimit`** |
| Python 下的真瓶颈 | **函数调用次数**，不是递归深度 |
| Python 写法 | 必须**非递归**，展开成两个循环 |
| 懒标记三铁律 | 完全覆盖打标记返回 / 下行前 push / 回溯后 pull |
| 双标记复合 | $b \leftarrow b \cdot k_{new} + b_{new}$，**顺序不能反** |
| 势能分析 | 区间开根/取模：总工作量 $O(n\log\log V)$ |
| 跳过已稳定位置 | **并查集** `nxt[i]` |
| 什么时候才写它 | 信息**不可减**时（最值、区间赋值、复杂标记） |

| 数据规模 → Python 现实性 |
| --- |
| $n, q \le 10^5$，非递归 | ⚠️ 险，2 秒限制下可能超 |
| $n, q \le 10^5$，递归 | ❌ 基本不可能 |
| $n, q \le 5\times10^5$，非递归 | ⚠️ CPython 不行，**PyPy3 可以**（BISHI130） |

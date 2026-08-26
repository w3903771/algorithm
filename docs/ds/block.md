---
id: ds/block
title: 分块
volume: 2
lang: py
---

# 第 39B 章　分块

<!-- CHAPTER-EXAMPLES -->
> **前置**：[序列与数组](array.md)、[前缀和与差分](../basic/prefix-sum.md)

分块是「优雅的暴力」：把序列切成每块 $\sqrt n$ 个，整块打标记、散块暴力。
作用在一维序列上的这种形态也叫**块状数组**，与树上分块、值域分块是同一套思想的不同载体；本章一律称「分块」。
复杂度 $O(\sqrt n)$ 比不过线段树的 $O(\log n)$，但它有两个别人没有的好处——
**不要求信息可合并**，以及**散块可以整段下沉到 C 层**（切片、`sum`、`bisect`）。

后一条让分块在 Python 里的地位和在 C++ 里完全不同：遇到「操作很怪」
（区间开根、区间小于计数、位运算）而线段树不好维护时，分块往往是唯一的路。
选型决策表（哪种情况该用哪种结构）在 [数据结构目录页](index.md)。

---

## 1　思路与模板

**思路**：把长度 $n$ 的序列切成每块 $S$ 个，每块维护 `sum` 和整体增量 `offset`。

- 区间修改：**整块**直接改 `offset`（$O(1)$）；**两端零散**的暴力改（$O(S)$）；
- 区间查询：整块用 `sum + num * offset`；零散的暴力累加。

伪代码：

```text
BLOCK_ID(k): (k - 1) / S
L(k): S * k + 1
R(k): min(S * (k + 1), n)

function modify(int l, int r, int v):
    for i in [BLOCK_ID(l), BLOCK_ID(r)]:
        if l <= L(i) and R(i) <= r: offset[i] += v          // 整块
        else: for j in [max(l,L(i)), min(r,R(i))]: sum[i], A[j] += v
```

---

## 2　块长为什么取 $\sqrt n$

推导如下：

> 每次最多有两个块是块内单独修改，这样的修改最多进行 $2S$ 次。
> 序列被分为 $\lceil n/S \rceil$ 块，这也是整块操作的最大次数。
> 考虑总代价 $2S + n/S$，根据均值不等式：
> $$2S + n/S \ge 2\sqrt{2n}, \quad \text{当且仅当 } S = \sqrt{n/2}$$

所以块长取 $\Theta(\sqrt n)$，总复杂度 $O(\sqrt n)$ 每次操作。

```python
import math


class Block:
    """分块：区间加 + 区间和。单次 O(sqrt n)。

    分块的价值不在复杂度（比线段树差），而在**灵活**：
    任何「整块能 O(1) 维护、散块能暴力」的信息都能用分块，
    包括线段树难以处理的「区间开根」「区间小于计数」等。
    """

    def __init__(self, a):
        n = len(a)
        self.n = n
        self.S = max(1, int(math.isqrt(n)))              # 块长取 sqrt(n)，理由见上面的推导
        self.nb = (n + self.S - 1) // self.S             # 向上取整得块数，末块可能不满
        self.a = list(a)                                 # a[i] 存「不含整块偏移」的值
        self.off = [0] * self.nb                         # off[b]：整块 b 欠着的统一增量
        self.sum = [0] * self.nb                         # sum[b]：块内 a 的和，同样不含 off
        for i, v in enumerate(a):
            self.sum[i // self.S] += v                   # i // S 就是 i 所属的块号
        # 循环不变量：块 b 的真实和 = sum[b] + off[b] * 块长

    def range_add(self, l, r, v):
        S, a, off, sm = self.S, self.a, self.off, self.sum
        bl, br = l // S, r // S                          # 左右端点各自所属的块号
        if bl == br:                                     # 同一块，全暴力
            for i in range(l, r + 1):
                a[i] += v
            sm[bl] += v * (r - l + 1)                    # 块和同步跟着涨
            return                                       # 提前返回，避免下面按跨块公式算重
        for i in range(l, (bl + 1) * S):                 # 左散块：从 l 补到块尾
            a[i] += v
        sm[bl] += v * ((bl + 1) * S - l)                 # 改了几个元素就加几份 v
        for b in range(bl + 1, br):                      # 中间整块，O(1)
            off[b] += v                                  # 只记账，块内元素一个不动
        for i in range(br * S, r + 1):                   # 右散块：从块首补到 r
            a[i] += v
        sm[br] += v * (r - br * S + 1)

    def query(self, l, r):
        S, a, off, sm, n = self.S, self.a, self.off, self.sum, self.n
        bl, br = l // S, r // S
        res = 0
        if bl == br:                                     # 同块：扫一段，再补这段的欠账
            for i in range(l, r + 1):
                res += a[i]
            return res + off[bl] * (r - l + 1)
        end = (bl + 1) * S                               # 左散块的右开边界（下一块的起点）
        for i in range(l, end):
            res += a[i]
        res += off[bl] * (end - l)                       # 散块也要补上所在整块的欠账
        for b in range(bl + 1, br):
            res += sm[b] + off[b] * min(S, n - b * S)    # 末块不满，长度取 min 防多算
        start = br * S                                   # 右散块的起点（块首）
        for i in range(start, r + 1):
            res += a[i]
        res += off[br] * (r - start + 1)
        return res
```

---

## 3　分块在 Python 里的特殊地位

| | 线段树 | 分块 |
| --- | --- | --- |
| 复杂度 | $O(\log n)$ | $O(\sqrt n)$ |
| 每次操作的 Python 层迭代 | $\approx 120$ | $\approx 3\sqrt n$（$n=10^5$ 时约 $950$） |
| 能否用 C 层加速 | ❌ 难 | ✅ **散块可以用切片、`sum`、`bisect`** |
| 灵活性 | 需要信息可合并 | **只要「整块可维护 + 散块可暴力」** |

**分块在 Python 里的救命之处是「散块能下沉到 C 层」**：

```python
res += sum(a[l:end])                   # ✅ C 层循环，比 for 快 30 倍
a[l:end] = [v + x for v in a[l:end]]   # ✅ 列表推导式，比逐个改快 3 倍
cnt += bisect_left(srt[b], x)          # ✅ C 层二分
```

这能把分块的实际常数压到和线段树同一量级，甚至更好。

---

---

## 4　例题

<!-- CHAPTER-EXAMPLE-TABLE -->

### BISHI129 区间增量与区间小于计数（中等）

> $n, q \le 10^5$，$|a_i| \le 10^7$。
> `1 l r x` 区间加 $x$；`2 l r x` 查询区间内**小于 $x$** 的元素个数（$|x| \le 10^9$）。
> 时限：C/C++ 5 秒，**其他语言 10 秒**。
> 题面见 [原题](https://www.nowcoder.com/practice/74481dd14e3b4875a190952f86e6ffab)。

**「区间小于计数」不满足可合并性**（两个子区间的答案无法合并成父区间的答案，
因为阈值 $x$ 是查询时才给的），**所以线段树不好做，分块是标准解**。

做法：每块额外维护一份**块内元素的排序副本** `srt[b]`。

| 操作 | 整块 | 散块 |
| --- | --- | --- |
| 区间加 | `off[b] += x`，排序副本不变（整体平移不改变顺序） | 逐个改 `a[i]`，然后**重建** `srt[b]` |
| 小于计数 | `bisect_left(srt[b], x - off[b])`，**C 层二分** | 逐个比较 |

```python
import sys
from bisect import bisect_left


def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); q = int(data[1])
    a = [int(v) for v in data[2:2 + n]]      # a[i] 存「不含整块偏移」的值

    S = 700                                  # 块长，需要实测调优
    nb = (n + S - 1) // S                    # 向上取整得块数
    off = [0] * nb                           # off[b]：整块 b 欠着的统一增量
    srt = [sorted(a[b * S:(b + 1) * S]) for b in range(nb)]  # 每块一份排序副本，供二分用
    # 循环不变量：位置 i 的真实值 = a[i] + off[i // S]；srt[b] 是 a 在块 b 内的有序版本

    p = 2 + n                                # token 游标；本题每条操作固定 4 个 token
    out = []
    push = out.append
    for _ in range(q):
        op = data[p]
        l = int(data[p + 1]) - 1             # 转 0-indexed
        r = int(data[p + 2]) - 1
        x = int(data[p + 3])
        p += 4
        bl, br = l // S, r // S              # 左右端点所属块号
        if op == b"1":                       # 区间加
            if bl == br:                     # 同块：整段都是散块，改完重排这一块
                for i in range(l, r + 1):
                    a[i] += x
                srt[bl] = sorted(a[bl * S:(bl + 1) * S])
            else:
                end = (bl + 1) * S           # 左散块的右开边界
                for i in range(l, end):
                    a[i] += x
                srt[bl] = sorted(a[bl * S:end])          # 只有部分元素变，顺序被打乱，必须重排
                for b in range(bl + 1, br):
                    off[b] += x              # 整块只改偏移，排序副本不动
                start = br * S               # 右散块起点（块首）
                for i in range(start, r + 1):
                    a[i] += x
                srt[br] = sorted(a[start:min((br + 1) * S, n)])  # 末块不满，右边界要夹到 n
        else:                                # 小于 x 计数
            cnt = 0
            if bl == br:
                v = x - off[bl]              # 阈值反向平移，就不必把 off 加回每个元素
                for i in range(l, r + 1):
                    if a[i] < v:
                        cnt += 1
            else:
                end = (bl + 1) * S
                v = x - off[bl]
                for i in range(l, end):      # 左散块：逐个比，因为只要其中一部分
                    if a[i] < v:
                        cnt += 1
                for b in range(bl + 1, br):
                    cnt += bisect_left(srt[b], x - off[b])    # C 层二分
                    # bisect_left 返回严格小于阈值的元素个数，正是本题要的「小于」
                start = br * S
                v = x - off[br]
                for i in range(start, r + 1):        # 右散块：同样逐个比
                    if a[i] < v:
                        cnt += 1
            push(cnt)
    sys.stdout.write("\n".join(map(str, out)) + "\n")


main()
```

**为什么整块加不用重排？** 整块所有元素加同一个数，**相对顺序不变**，
所以排序副本可以保持不动，只需要在比较时把阈值反向平移（`x - off[b]`）。
这是分块维护有序信息的核心技巧。

**Python 现实性判断**：

| 项 | 每次查询的代价 | 总量（$q=10^5$） |
| --- | --- | --- |
| 整块二分（$n/S = 143$ 次 `bisect`） | 143 次 C 层调用 | $1.4\times10^7$ 次 C 调用 |
| 散块暴力（最多 $2S = 1400$ 次比较） | 1400 次 Python 迭代 | $1.4\times10^8$ 次 |

**散块的 $1.4\times10^8$ 次 Python 层迭代是致命的**（约 60–100 秒）。

**必须的优化**：把散块也下沉到 C 层。

```python
# ❌ Python 层逐个比较
for i in range(l, end):
    if a[i] < v:
        cnt += 1

# ✅ C 层：切片 + sorted + bisect（切片和排序都是 C 层）
seg = a[l:end]
seg.sort()
cnt += bisect_left(seg, v)
```

对 $\le 700$ 个元素排序约 30 μs，两个散块 $\times 10^5$ 次查询 = 6 秒，
**贴着 10 秒的上限但能过**。减小块长 $S$ 能降低散块成本但会增加整块二分次数，
实测 $S$ 在 $[300, 700]$ 之间都可行，取 400 较稳。

> **诚实结论**：BISHI129 在 Python 3.9 下**属于高难度**，
> 需要把散块和整块两条路径都压到 C 层，并对块长做实测调优。
> 这是一道**语言劣势明显**的题——同样的分块在 C++ 里随手就过。

题解：[`solutions/nowcoder/BISHI129/sol.py`](../solutions/BISHI129.md)（已通过判题机验证，Python 3）

---

## 5　本章速查

| 要点 | 结论 |
| --- | --- |
| 块长 | $\Theta(\sqrt n)$，实战需实测调优 |
| 整块 / 散块 | 整块改标记 $O(1)$，散块暴力 $O(\sqrt n)$ |
| Python 下的优势 | **散块能用切片 / `sum` / `bisect` 下沉到 C 层** |
| 适用信号 | 操作很怪（开根、小于计数、位运算），线段树不好维护 |
| 不适用 | 需要合并信息且规模大时，仍应回到线段树 |

| 数据规模 → Python 现实性 |
| --- |
| $n, q \le 10^5$ | ⚠️ 险，需把两条路径都压到 C 层 |
| $n, q \le 5\times10^5$（每次触及 $O(\sqrt n)$ 块） | ❌ 不可能，**换 PyPy 也不行** |

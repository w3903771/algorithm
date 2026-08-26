---
id: basic/prefix-sum
title: 前缀和与差分
volume: 1
lang: py
---

# 第 42 章　前缀和与差分

<!-- CHAPTER-EXAMPLES -->

前缀和与差分是**一对互逆运算**，也是竞赛里性价比最高的一组技巧：
十行代码，把「大量区间查询」或「大量区间修改」从 $O(nq)$ 降到 $O(n + q)$。

一句话记忆：

> **前缀和管「查」，差分管「改」；前缀和是差分的逆，差分是前缀和的逆。**

| 需求 | 工具 | 预处理 | 单次操作 |
| --- | --- | --- | --- |
| 数组不变，大量**区间求和** | 前缀和 | $O(n)$ | $O(1)$ |
| 大量**区间加**，最后统一输出 | 差分 | $O(1)$ | $O(1)$ + 末尾 $O(n)$ |
| **又改又查** | 树状数组 / 线段树 | $O(n)$ | $O(\log n)$ |

第三行才是 [树状数组](../ds/fenwick.md) 与 [线段树](../ds/segment-tree.md) 的领域。
**只要没有「边改边查」，就不要上数据结构**——前缀和 / 差分又短又快。

---

## 1　一维前缀和

定义 $S_0 = 0$，$S_i = a_1 + a_2 + \cdots + a_i$，则

$$\sum_{i=l}^{r} a_i = S_r - S_{l-1}$$

**「多开一位 $S_0 = 0$」是这个公式成立的全部秘密**——有了它，$l = 1$ 时不用特判。

```python
from itertools import accumulate

# a 是 0-indexed 的列表；pre 前面补一个 0，长度变成 n+1
# 下标对应关系：pre[i+1] = a[0] + ... + a[i]，即 pre 比 a 整体右移一位
# 换成 1-indexed 的说法就是 pre[i] = a_1 + ... + a_i，且 pre[0] = 0
pre = [0] + list(accumulate(a))

# 查询原数组下标 [l, r]（1-indexed，对应 a[l-1..r-1]）的和
# 左端减的是 pre[l-1] 而不是 pre[l]：要把 a_l 本身留在结果里，边界必须退一格
s = pre[r] - pre[l - 1]
```

`itertools.accumulate` 把累加循环整个下沉到 C 层，$n = 10^6$ 时比手写 `for` 快约 5 倍：

```python
# ❌ Python 层循环，1e6 次
pre = [0] * (n + 1)                   # 长度 n+1：多出来的那一位就是 pre[0] = 0
for i in range(n):
    pre[i + 1] = pre[i] + a[i]        # 下标偏移：写入 pre[i+1]，它收纳的是 a[0..i]

# ✅ C 层循环
pre = [0] + list(accumulate(a))       # accumulate 只产出 n 项，补上 0 才凑够 n+1 项
```

> `accumulate` 还能换运算：`accumulate(a, max)` 求前缀最大值，
> `accumulate(a, operator.mul)` 求前缀积，`accumulate(a, operator.xor)` 求前缀异或。
> **前缀异或**特别常用——异或的逆运算是自己，所以区间异或 $= pre_r \oplus pre_{l-1}$。

### 前缀和能处理的运算

| 运算 | 可用？ | 区间查询式 |
| --- | --- | --- |
| 加法 | ✅ | $S_r - S_{l-1}$ |
| 异或 | ✅ | $S_r \oplus S_{l-1}$ |
| 乘法 | ⚠️ | 需要逆元，且有 0 就崩，见 [快速幂与逆元](../math/number/inverse.md) |
| 最大 / 最小 | ❌ | **没有逆运算**，要用 ST 表，见 [倍增](binary-lifting.md) |

> **判据：前缀和要求该运算有逆元（构成群）。** 加法、异或有，`max` 没有。
> 这就是为什么区间最值必须换成 ST 表或线段树。

---

## 2　一维差分

差分是前缀和的逆运算：$d_i = a_i - a_{i-1}$（约定 $a_0 = 0$），于是 $a_i = \sum_{j \le i} d_j$。

**区间加 $[l, r] \mathrel{+}= k$ 在差分数组上只是两次单点修改**：

$$d_l \mathrel{+}= k, \qquad d_{r+1} \mathrel{-}= k$$

一个很形象的说法：「$a_l$ 比前一个元素多了 $k$；$a_{r+1}$ 比前一个元素少了 $k$」。

```python
# 有效下标是 1..n，再多开 d[n+1] 当哨兵：r = n 时 d[r+1] 不越界
d = [0] * (n + 2)

def range_add(l, r, k):           # 1-indexed 区间 [l, r] 加 k
    d[l] += k                     # 从 l 起，每个位置都比它前一个多了 k
    d[r + 1] -= k                 # 在 r+1 处把这个 k 撤回，影响正好止于 r

# 全部操作做完后，对 d 求一次前缀和即还原出每个位置的最终值
# 切片 d[1:n+1] 取的是下标 1..n；哨兵位 d[n+1] 只用来吸收减法，不参与输出
final = list(accumulate(d[1:n + 1]))
```

**「多开一位」是差分的标配**：$r = n$ 时 `d[r+1]` 就是那个哨兵位，它的值永远不会被用到。
不开就得写 `if r + 1 <= n`，白白多一处出错机会。

| 差分数组的三种常见形态 | 写法 |
| --- | --- |
| 数组本来就有初值 $a$ | 差分只记「增量」，最后 `a[i] + 增量[i]` |
| 数组初值全 0 | 差分即答案，前缀和一次还原 |
| 只关心某一位 | 不用还原整个数组，只对该位求前缀和 |

---

## 3　二维前缀和

$$S_{i,j} = \sum_{x \le i}\sum_{y \le j} a_{x,y}$$

递推式（**容斥**，减去重复的左上角）：

$$S_{i,j} = S_{i-1,j} + S_{i,j-1} - S_{i-1,j-1} + a_{i,j}$$

还有一个更省心的等价写法：**先算行内前缀 `pre`，再加上一行的 $S$**，
这样只有一次加法，不用做减法：

```python
S[i][j] = S[i - 1][j] + (a[i][1] + ... + a[i][j])
```

子矩阵求和（左上 $(x_1,y_1)$、右下 $(x_2,y_2)$）：

$$\text{sum} = S_{x_2,y_2} - S_{x_1-1,y_2} - S_{x_2,y_1-1} + S_{x_1-1,y_1-1}$$

**四项容斥的记法**：大矩形 − 上面一条 − 左边一条 + 左上角（被减了两次要补回来）。

```python
from itertools import accumulate

# 读入 n 行、每行 m 个数，建 (n+1) x (m+1) 的前缀和矩阵，下标从 1 开始
# 下标对应关系：S[i][j] 是原矩阵左上角到第 i 行第 j 列这块子矩阵的和
S = [[0] * (m + 1)]                               # 第 0 行全 0，使 x1 = 1 时不必特判
for i in range(n):
    row = accumulate(rows[i])                     # 行内前缀，C 层
    prev = S[-1]                                  # 上一行（第 i-1 行）已算好的 S
    cur = [0]                                     # 每行的第 0 列也补 0，使 y1 = 1 时不必特判
    for j, v in enumerate(row, 1):                # 从 1 开始计数：v 是本行前 j 个元素之和
        cur.append(v + prev[j])                   # 本行前缀 + 上一行的 S = 本格的 S
    S.append(cur)


def query(x1, y1, x2, y2):
    # 四项容斥：大矩形 - 上面一条 - 左边一条 + 左上角（被减了两次，补回来一次）
    # 两个减号项用 x1-1 / y1-1：第 x1 行和第 y1 列要保留，所以边界各退一格
    return S[x2][y2] - S[x1 - 1][y2] - S[x2][y1 - 1] + S[x1 - 1][y1 - 1]
```

---

## 4　二维差分

区间加的二维版：给子矩阵 $(x_1,y_1)$–$(x_2,y_2)$ 整体加 $k$，在差分矩阵上是**四次单点修改**：

$$d_{x_1,y_1} \mathrel{+}= k,\quad d_{x_1,y_2+1} \mathrel{-}= k,\quad
d_{x_2+1,y_1} \mathrel{-}= k,\quad d_{x_2+1,y_2+1} \mathrel{+}= k$$

**符号与二维前缀和的四项容斥完全一致**（`+ - - +`），因为它们互为逆运算。

```python
# 有效下标是 1..n 与 1..m，两个方向各多开一位当哨兵（x2+1 最大到 n+1，y2+1 最大到 m+1）
d = [[0] * (m + 2) for _ in range(n + 2)]


def range_add_2d(x1, y1, x2, y2, k):
    d[x1][y1] += k                                # 左上角：从这里起整片加 k
    d[x1][y2 + 1] -= k                            # 右侧多出的一条，撤回
    d[x2 + 1][y1] -= k                            # 下方多出的一条，撤回
    d[x2 + 1][y2 + 1] += k                        # 右下角被撤了两次，补回来一次


# 全部操作完成后，对 d 做一次二维前缀和，得到每格的增量
prev = [0] * (m + 2)                              # 第 0 行的二维前缀和全 0
for i in range(1, n + 1):
    row = list(accumulate(d[i]))                  # 先做行内前缀（列方向的累加）
    row = list(map(int.__add__, row, prev))       # 再加上一行的结果，整行在 C 层相加
    prev = row
    # row[j] 就是格子 (i, j) 的增量
```

> **`map(int.__add__, x, y)` 是逐元素加两个列表的最快写法**，
> 比 `[x[i] + y[i] for i in range(len(x))]` 快 2–3 倍，
> 因为它省掉了下标运算和 Python 层循环体。
> 二维题里 $n \times m$ 到 $10^6$ 时，这一条就是 AC 与 TLE 的分界。

### 四种组合的完整对照

| | 一维 | 二维 |
| --- | --- | --- |
| **前缀和**（查） | $S_r - S_{l-1}$，2 项 | 4 项容斥 |
| **差分**（改） | $d_l \mathrel{+}= k$，$d_{r+1} \mathrel{-}= k$，2 处 | 4 处，符号 `+ - - +` |
| 还原 | 一次前缀和 | 一次二维前缀和 |
| 边界 | 多开 1 位 | 两个方向各多开 1 位 |

---

## 5　前缀和的四个经典变形

| 变形 | 式子 | 用途 |
| --- | --- | --- |
| **前缀和之差为定值** | 求 $S_r - S_{l-1} = k$ 的对数 | 用 `Counter` 统计 $S$，见[桶计数与离散化 §5](discretization.md) |
| **前缀和取模** | $S_r \equiv S_{l-1} \pmod m$ | 区间和被 $m$ 整除的子段计数 |
| **前缀异或** | $X_r \oplus X_{l-1}$ | 区间异或、异或为 0 的子段 |
| **前缀最值** | `accumulate(a, max)` | 只能查前缀，不能查任意区间 |

其中第一种最常考，套路是：

```python
# 求「和恰好为 k 的连续子段」数量，O(n)
from collections import Counter

# 枚举右端点：设当前前缀和为 s，子段 (j, i] 的和就是 s - S_j
cnt = Counter([0])           # S_0 = 0 代表空前缀，必须计入，否则漏掉从头开始的子段
s = ans = 0
for x in a:
    s += x                   # s 是以当前元素结尾的前缀和
    ans += cnt[s - k]        # 和为 k 等价于 S_j = s - k，数一数有多少个这样的左端点
    cnt[s] += 1              # 先查询再登记，避免把自己当左端点（那会算出长度为 0 的子段）
```

**这个模式（枚举右端点 + 用哈希表查左端点）是「子段计数」类题目的通用解法**，
它和 41.5 的「差值桶」是同一个思想的两种外衣。

---

## 6　树上差分（简介）

序列上的差分搬到树上：给路径 $u \to v$ 上的所有点加 $k$，
可以只在四个点上打标记，最后做一次**子树求和**（DFS 回溯时累加）。

| 类型 | 标记 |
| --- | --- |
| **点差分** | $d_u \mathrel{+}= k$，$d_v \mathrel{+}= k$，$d_{\text{lca}} \mathrel{-}= k$，$d_{\text{fa(lca)}} \mathrel{-}= k$ |
| **边差分** | $d_u \mathrel{+}= k$，$d_v \mathrel{+}= k$，$d_{\text{lca}} \mathrel{-}= 2k$ |

它需要 LCA 作为前置，见 [倍增](binary-lifting.md) 与
[LCA 与树上路径](../graph/tree/lca.md)。
NOIp 2015《运输计划》就是「二分答案 + 树上差分」的经典组合，见
[二分](binary-search.md)。

---

## 7　例题

<!-- CHAPTER-EXAMPLE-TABLE -->

### BISHI110　【模板】静态区间和（简单）

> $n, q \le 10^6$，$|a_i| \le 10^9$。$q$ 次询问区间和。
> 题面见 [原题](https://www.nowcoder.com/practice/ac79a1a4a66646cc87525d6faa86e021)。

模板题，但 $n = q = 10^6$ 让它变成了一道**卡常题**：输入有 $3\times10^6$ 个 token，
输出有 $10^6$ 行。

```python
import sys
from itertools import accumulate


def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); q = int(data[1])
    # 前面补 0，下标偏移一位：pre[i] = a1 + .. + ai，pre[0] = 0，总长 n+1
    pre = [0] + list(accumulate(map(int, data[2:2 + n])))     # pre[i] = a1+..+ai
    qs = list(map(int, data[2 + n:2 + n + 2 * q]))            # 询问也一次性转成 int
    # 每个询问占 2 个 token：qs[i] 是 l、qs[i+1] 是 r（均 1-indexed）
    # 区间和 = pre[r] - pre[l-1]，左端退一格才能把 a_l 本身留下
    out = [pre[qs[i + 1]] - pre[qs[i] - 1] for i in range(0, 2 * q, 2)]
    sys.stdout.write("\n".join(map(str, out)) + "\n")


main()
```

四个提速点，缺一个都可能 TLE：

- **`sys.stdin.buffer.read().split()`** 一次性读完，见
  [输入输出处理](../toolkit/io.md)。
- **`accumulate` 建前缀和**，而不是 Python 层 `for`。
- **询问用 `list(map(int, ...))` 批量转换**，而不是循环里逐个 `int()`。
  $2\times10^6$ 次 `int()` 调用，批量 `map` 能省一半时间。
- **输出 `"\n".join`**，逐行 `print` 在 $10^6$ 行时是灾难。

> $|a_i| \le 10^9$、$n \le 10^6$，区间和最大到 $10^{15}$——C++ 必须开 `long long`，
> **Python 的 `int` 无上限，这一条不用管**。这是 Python 在前缀和题上的天然优势。

### BISHI111　【模板】差分（简单）

> $n, m \le 10^5$，$m$ 次区间加，最后输出整个数组。
> 题面见 [原题](https://www.nowcoder.com/practice/4bbc401a5df140309edd6f14debdba42)。

差分的裸模板：

```python
import sys
from itertools import accumulate


def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); m = int(data[1])
    a = list(map(int, data[2:2 + n]))
    d = [0] * (n + 1)                     # 差分数组，下标 0..n（d[n] 是哨兵，不对应任何元素）
    p = 2 + n                             # p 是当前待读 token 的位置，每条操作前移 3 格
    for _ in range(m):
        l = int(data[p]); r = int(data[p + 1]); k = int(data[p + 2]); p += 3
        d[l - 1] += k                     # 题面 1-indexed 的 l 对应 a[l-1]，加号打在这里
        d[r] -= k                         # 题面的 r+1 对应 a[r]，减号打在这里；r == n 时正好是哨兵位
    add = accumulate(d)                   # 前缀和还原：add 的第 i 项就是 a[i] 收到的总增量
    sys.stdout.write(" ".join(map(str, map(int.__add__, a, add))) + "\n")


main()
```

两个细节：

- **下标转换**：题目是 1-indexed，代码用 0-indexed，所以 `d[l-1] += k`、`d[r] -= k`。
  写完一定要用样例手算一遍——**差分题的错误 90% 出在这一格上**。
- **`map(int.__add__, a, add)`**：`a` 是原数组、`add` 是增量生成器，
  两者逐元素相加全在 C 层完成，`zip` 会在较短的那个（`a`，长度 $n$）处停止，
  哨兵位自动被丢掉。

> 题面备注里写着「建议使用 PyPy 而不是 Python」。这是判题平台对模板题的通用提示，
> 但只要按上面的写法（整块 IO + `accumulate` + `map`），CPython 也能轻松过。
> **把循环下沉到 C 层，就是 Python 选手的 PyPy。**

### BISHI112　【模板】二维前缀和（中等）

> $n, m \le 10^3$，$q \le 10^5$，$|a_{i,j}| \le 10^9$。
> 题面见 [原题](https://www.nowcoder.com/practice/99eb8040d116414ea3296467ce81cbbc)。

```python
import sys
from itertools import accumulate


def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); m = int(data[1]); q = int(data[2])
    p = 3                                                # 矩阵数据从第 3 个 token 开始
    S = [[0] * (m + 1)]                                  # 第 0 行全 0，让 x1 = 1 时不用特判
    for i in range(n):
        row = accumulate(map(int, data[p:p + m]))        # 行内前缀和
        p += m
        prev = S[-1]                                     # 上一行的二维前缀和
        cur = [0]                                        # 第 0 列也补 0，让 y1 = 1 时不用特判
        ap = cur.append
        for j, v in enumerate(row, 1):                   # v 是本行前 j 个元素之和
            ap(v + prev[j])                              # 再加上一行的 S，得到 S[i+1][j]
        S.append(cur)

    out = []
    qs = data[p:p + 4 * q]                               # 每个询问 4 个 token
    for i in range(0, 4 * q, 4):
        x1 = int(qs[i]); y1 = int(qs[i + 1])
        x2 = int(qs[i + 2]); y2 = int(qs[i + 3])
        # 四项容斥；减号项用 x1-1 / y1-1，第 x1 行与第 y1 列要留在答案里
        out.append(S[x2][y2] - S[x1 - 1][y2] - S[x2][y1 - 1] + S[x1 - 1][y1 - 1])
    sys.stdout.write("\n".join(map(str, out)) + "\n")


main()
```

- **多开一行一列全 0**（下标从 1 开始），这样 $x_1 = 1$ 或 $y_1 = 1$ 时不用特判。
- **用两步递推**（先行内前缀，再加上一行），比四项容斥递推少一次减法，
  在 $10^6$ 个格子上能省下可观的时间。
- **`ap = cur.append` 提前绑定**，省掉 $10^6$ 次属性查找，见
  [复杂度与 Python 性能](../toolkit/complexity.md)。

### BISHI113　【模板】二维差分（中等）

> $n, m \le 10^3$，$q \le 10^5$ 次子矩阵加，最后输出整个矩阵。
> 题面见 [原题](https://www.nowcoder.com/practice/50e1a93989df42efb0b1dec386fb4ccc)。

```python
import sys
from itertools import accumulate


def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); m = int(data[1]); q = int(data[2])
    p = 3 + n * m                                  # 先跳过矩阵，稍后再按需取用
    d = [[0] * (m + 2) for _ in range(n + 2)]      # 差分矩阵，两个方向各多开一位当哨兵
    for _ in range(q):
        x1 = int(data[p]); y1 = int(data[p + 1])
        x2 = int(data[p + 2]); y2 = int(data[p + 3]); k = int(data[p + 4]); p += 5
        d[x1][y1] += k                             # 左上角起整片加 k
        d[x1][y2 + 1] -= k                         # 撤回右侧多加的一条
        d[x2 + 1][y1] -= k                         # 撤回下方多加的一条
        d[x2 + 1][y2 + 1] += k                     # 右下角被撤两次，补回一次

    out = []
    prev = [0] * (m + 2)                                # 第 0 行的二维前缀和全 0
    pos = 3                                             # 回到矩阵原值区，逐行按需解析
    for i in range(1, n + 1):
        row = list(accumulate(d[i]))                    # 行内前缀
        row = list(map(int.__add__, row, prev))         # 加上一行 -> 二维前缀和
        prev = row
        base = data[pos:pos + m]; pos += m              # 该行的原始值
        # 差分矩阵 1-indexed、原始行 0-indexed，所以增量取 row[j+1] 对应 base[j]
        out.append(" ".join([str(int(base[j]) + row[j + 1]) for j in range(m)]))
    sys.stdout.write("\n".join(out) + "\n")


main()
```

三个要点：

- **四个角的符号 `+ - - +`**，和二维前缀和的四项容斥完全对称。写反一个就整片错。
- **两个方向都多开一位**：`y2 + 1` 最大到 $m+1$，`x2 + 1` 最大到 $n+1$，
  所以矩阵开 $(n+2) \times (m+2)$。
- **矩阵原值不必提前解析**：先跳到操作区读完全部操作，输出时再逐行 `int()`。
  这样原始矩阵只被遍历一次，省掉一个 $10^6$ 元素的中间列表。

### BISHI68　刷题统计（简单）

> 已知并集 $n$、三个集合大小 $a,b,c$、恰好属于两个集合的人数 $d$，求三个都属于的人数。
> 题面见 [原题](https://www.nowcoder.com/practice/99ddb1a6e71d47dcbbe4f272aba532b8)。

这题考的是**容斥**——二维前缀和的四项加减就是二维容斥，两者是同一套思想。

设 $e_1, e_2, e_3$ 分别是恰好属于 1 / 2 / 3 个集合的人数：

$$\begin{aligned}
n &= e_1 + e_2 + e_3 && \text{（并集，每人算一次）}\\
a + b + c &= e_1 + 2e_2 + 3e_3 && \text{（逐集合求和，属于 }k\text{ 个的人被数 }k\text{ 次）}\\
d &= e_2 && \text{（题目直接给出）}
\end{aligned}$$

相减得 $a+b+c-n = e_2 + 2e_3$，于是

$$e_3 = \frac{a+b+c-n-d}{2}$$

```python
import sys


def main():
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    out = []
    for i in range(t):
        # 每组 5 个 token，第 0 个 token 是组数，所以第 i 组从下标 1 + 5i 开始
        n = int(data[1 + 5 * i]); a = int(data[2 + 5 * i]); b = int(data[3 + 5 * i])
        c = int(data[4 + 5 * i]); d = int(data[5 + 5 * i])
        # a+b+c-n = e2 + 2*e3，再减去 d = e2，剩下 2*e3；整除 2 不会有精度问题
        out.append(str((a + b + c - n - d) // 2))
    sys.stdout.write("\n".join(out) + "\n")


main()
```

> **坑**：$d$ 的定义是「**恰好**属于两个集合的人数」，不是
> $|A\cap B| + |B\cap C| + |A\cap C|$（后者会把三个都属于的人重复计 3 次）。
> 按后一种定义符号会整个反过来，样例立刻对不上。
> **容斥题一定要先把「恰好 $k$ 个」和「至少 $k$ 个」分清楚。**

题解见 [`solutions/nowcoder/BISHI68/sol.py`](../solutions/BISHI68.md)。
容斥原理的系统讲法见 [组合数学](../math/combi/basic.md)。

---

### 另一处题库里的两道前缀和题

**[LC560](../solutions/LC560.md)** 就是上面「和恰好为 $k$ 的连续子段」那段模板的原题：
枚举右端点，用哈希表记「每个前缀和出现过几次」，
当前前缀和为 $s$ 时把 `cnt[s - k]` 累加进答案，一遍扫描 $O(n)$。
哈希表要预置 `cnt[0] = 1`，否则从下标 $0$ 起算的那些子段会被整批漏掉。
**这题不能用滑动窗口**——元素允许为负，窗口和不随右端点单调，收缩条件无从写起。

**[LC238](../solutions/LC238.md)：前缀积 ＋ 后缀积。**
题面不许用除法，而且数组含 $0$ 时除法本来就失效，
答案只能拆成「$i$ 左边所有数之积」乘「$i$ 右边所有数之积」。
两遍扫描：第一遍从左往右把前缀积写进结果数组，第二遍从右往左用一个标量滚动后缀积并就地相乘，
$O(n)$ 时间，除输出数组外额外空间 $O(1)$。
前缀和换成前缀积之后，**差分那一半失效了**——除法在含 $0$ 时不可逆，
所以只能双向各扫一遍，不能像前缀和那样一减了事。

## 8　本章速查

| 需求 | 工具 |
| --- | --- |
| 数组固定 + 大量区间查 | **前缀和**，$O(n)$ 预处理 + $O(1)$ 查 |
| 大量区间改 + 最后一次输出 | **差分**，$O(1)$ 改 + $O(n)$ 还原 |
| 又改又查 | 树状数组 / 线段树，$O(\log n)$ |
| 区间最值 | 前缀和**不适用**（无逆元），用 ST 表 |
| 建前缀和 | `[0] + list(accumulate(a))` |
| 逐元素加两个列表 | `map(int.__add__, x, y)` |
| 差分数组长度 | **多开一位**做哨兵 |
| 二维前缀和查询 | `S[x2][y2] - S[x1-1][y2] - S[x2][y1-1] + S[x1-1][y1-1]` |
| 二维差分修改 | 四个角 `+ - - +` |
| 和为 $k$ 的子段计数 | 前缀和 + `Counter`，$O(n)$ |
| 区间异或 | 前缀异或，`accumulate(a, xor)` |
| 路径加 + 子树查 | 树上差分（需 LCA） |

| 模板 | 位置 |
| --- | --- |
| 一维前缀和 / 差分 | §1、§2 |
| 二维前缀和 / 差分 | §3、§4 |
| 和为 $k$ 的子段计数 | §5 |
| 树上差分标记 | §6 |

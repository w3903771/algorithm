---
id: ds/sparse-table
title: ST 表
volume: 2
lang: py
---

# 第 39C 章　ST 表

<!-- CHAPTER-EXAMPLES -->
> **前置**：[序列与数组](array.md)、[倍增](../basic/binary-lifting.md)

**只有查询、没有修改**的区间最值——这类问题通称 **RMQ**（Range Minimum/Maximum Query）——用不着线段树：
ST 表 $O(n\log n)$ 预处理、
**$O(1)$ 查询**，而且预处理能整层交给 C 层的 `map` 完成。

代价是不支持修改，空间 $O(n\log n)$。一旦题目出现「修改」，就得换
[线段树](segment-tree.md) 或[树状数组](fenwick.md)。选型决策表（哪种情况该用哪种结构）在 [数据结构目录页](index.md)。

---

## 1　原理与模板

**只有查询、没有修改**时，别用线段树，用 ST 表：$O(n\log n)$ 预处理、**$O(1)$ 查询**。

原理：$st[k][i]$ 表示区间 $[i,\ i + 2^k)$ 的最值。倍增递推

$$st[k][i] = \max\big(st[k-1][i],\ st[k-1][i + 2^{k-1}]\big)$$

查询 $[l, r]$ 时取 $k = \lfloor \log_2 (r-l+1) \rfloor$，
用**两个可重叠**的长度 $2^k$ 区间覆盖：

$$\max(l, r) = \max\big(st[k][l],\ st[k][r - 2^k + 1]\big)$$

（最值满足**可重复贡献**，重叠不影响结果；求和就不行。）

```python
class SparseTable:
    """ST 表：静态区间最值。预处理 O(n log n)，查询 O(1)。

    Python 关键：每层用 map(max, ...) 在 **C 层**构建，
    而不是写 Python 循环 —— 这是能否通过大数据的分水岭。
    """

    def __init__(self, a, func=max):
        self.f = func
        n = len(a)
        self.st = st = [list(a)]                 # 第 0 层：长度 1 的区间，就是原数组
        k = 1
        while (1 << k) <= n:                     # 层数只到 log2(n)，再高的区间放不下
            prev = st[-1]                        # 上一层：每格代表长度 2^(k-1) 的区间
            half = 1 << (k - 1)                  # 两个半区间的起点相距 2^(k-1)
            # ★ 整层用 C 层的 map 构建，不写 Python for 循环
            st.append(list(map(func, prev, prev[half:])))
            # map 在较短的那个迭代器耗尽时停止，本层长度自动截成 n - 2^k + 1
            k += 1

    def query(self, l, r):
        """闭区间 [l, r] 的最值，O(1)。"""
        k = (r - l + 1).bit_length() - 1         # 最大的 k 使 2^k <= 区间长度
        row = self.st[k]
        # 两段长度 2^k 的区间：一段贴左端，一段贴右端。它们必然覆盖 [l, r]，
        # 中间重叠部分不影响结果（最值可重复贡献）。
        return self.f(row[l], row[r - (1 << k) + 1])
```

> **`list(map(max, prev, prev[half:]))` 是本模板的灵魂**：
> `map` 遇到较短的迭代器就停止，所以自动截断到正确长度，
> 而且整层构建全在 C 层完成。写成 Python 的
> `[max(prev[i], prev[i+half]) for i in range(...)]` 会慢 5 倍。

---

## 2　例题

<!-- CHAPTER-EXAMPLE-TABLE -->

### BISHI125 【模板】静态区间最值（中等）

> $n, q \le 5\times10^5$，$|a_i| \le 10^9$。
> `1 l r` 查区间最小值，`2 l r` 查区间最大值。
> 时限：C/C++ 5 秒，**其他语言 10 秒**；空间：其他语言 **2048M**。
> 题面见 [原题](https://www.nowcoder.com/practice/831a314449d44ea0b1db90ca626bcd1a)。

**只有查询、没有修改** → ST 表，不要写线段树。

需要**两张表**（min 和 max），各 $\lceil \log 5\times10^5 \rceil = 19$ 层。

```python
import sys


def main():
    data = sys.stdin.buffer.read().split()    # 一次性读入再切分，比逐行 input 快一个量级
    n = int(data[0]); q = int(data[1])
    a = list(map(int, data[2:2 + n]))        # 切片 [2, 2+n) 恰好是 n 个初值

    # 两张 ST 表，整层用 map 在 C 层构建
    mn = [a]                                 # mn[k][i]：区间 [i, i+2^k) 的最小值
    mx = [a]                                 # 两表共用同一个第 0 层对象：全程只读，不会互相污染
    k = 1
    while (1 << k) <= n:                     # 建到 2^k 超过 n 为止，共 log2(n) 层
        h = 1 << (k - 1)                     # 上一层两个半区间的起点间距
        p = mn[-1]
        mn.append(list(map(min, p, p[h:])))  # 与右移 h 的自己配对；map 遇短即停，长度自动收窄
        p = mx[-1]
        mx.append(list(map(max, p, p[h:])))
        k += 1

    p = 2 + n                                # p 改作 token 游标，此时指向第一条询问
    out = []
    push = out.append                        # 绑成局部名字，省掉每次询问的属性查找
    for _ in range(q):
        op = data[p]
        l = int(data[p + 1]) - 1             # 转 0-indexed
        r = int(data[p + 2]) - 1
        p += 3                               # 每条询问固定 3 个 token
        j = (r - l + 1).bit_length() - 1     # 最大的 j 使 2^j 不超过区间长度
        s = r - (1 << j) + 1                 # 右半段起点；与左半段重叠不影响最值
        if op == b"1":                       # data 未解码，比较对象是 bytes 而非 str
            row = mn[j]
            x = row[l]; y = row[s]
            push(x if x < y else y)          # 内联比较比调用内置 min 快约 20%
        else:
            row = mx[j]
            x = row[l]; y = row[s]
            push(x if x > y else y)
    sys.stdout.write("\n".join(map(str, out)) + "\n")


main()
```

**Python 现实性**：

| 项 | 量级 | 估时 |
| --- | --- | --- |
| 读入 + `map(int)` | $10^6$ 个 token | 0.5 s |
| 建两张 ST 表 | $2 \times 19 \times 5\times10^5 = 1.9\times10^7$ 次 C 层比较 | 2–3 s |
| $5\times10^5$ 次查询 | 每次约 10 次 Python 层操作 | 2–3 s |
| 输出 | $5\times10^5$ 行 | 0.3 s |

总计 5–7 秒，**在 10 秒限制内**。空间约 $1.9\times10^7$ 个指针 = 150MB，
加上 token 列表，在 2048MB 内。

**三个关键点**：

1. **整层用 `map(min, p, p[h:])` 构建**，写 Python 循环会慢 5 倍直接超时；
2. **查询里内联 `min`/`max`**（写成 `x if x < y else y`）比调用内置函数快约 20%，
   $10^6$ 次调用省下来是实打实的；
3. **不要建成三维 `st[k][i]` 的嵌套结构再逐个索引**——两级索引已经是极限。

> **另一条路**：$O(n)$ 的做法（分块 + 块内前后缀最值 + 块间 ST 表）能把空间降到 $O(n)$，
> 但查询时的 Python 层判断更多，实测未必更快。**空间够就用朴素 ST 表。**

题解：[`solutions/nowcoder/BISHI125/sol.py`](../solutions/BISHI125.md)（已通过判题机验证，Python 3）

---

## 3　本章速查

| 要点 | 结论 |
| --- | --- |
| 适用 | **静态**区间最值（可重复贡献的运算：max / min / gcd / 与 / 或） |
| 预处理 / 查询 | $O(n\log n)$ / **$O(1)$** |
| 不支持 | 修改 |
| 建表写法 | 整层 `list(map(max, p, p[h:]))`，**C 层构建**，写 Python 循环慢 5 倍 |
| 查询 | 取 $k = \lfloor\log_2(r-l+1)\rfloor$，两段长 $2^k$ 的区间覆盖，允许重叠 |

| 数据规模 → Python 现实性 |
| --- |
| 静态查询 $5\times10^5$ | ✅ 可行（靠 C 层建表） |

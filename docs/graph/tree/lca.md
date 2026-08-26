---
id: graph/tree/lca
title: LCA 与树上路径
volume: 2
lang: py
---

# 第 94A 章　LCA 与树上路径

<!-- CHAPTER-EXAMPLES -->
> **前置**：[树的基础与遍历](basic.md)、[倍增](../../basic/binary-lifting.md)、[ST 表](../../ds/sparse-table.md)

**LCA$(u,v)$** 是既是 $u$ 的祖先又是 $v$ 的祖先中深度最大的那个点。
求出它，两点间的一切就都是减法：路径边数、路径权和、路径异或和、判点在不在路径上。
再配上树上差分，「给路径上所有点加 $k$」也只要打四个标记。

三条主流路线（倍增 / Tarjan 离线 / 欧拉序 + ST 表）在 Python 下的取舍
和 C++ **完全不同**——Tarjan 在这里几乎从不划算，本章会给出实测依据。

---

## 1　树上两点路径长度

有了 LCA，路径长度就是一个减法：

$$\mathrm{dist}(u,v) = \mathrm{dep}[u] + \mathrm{dep}[v] - 2\,\mathrm{dep}[\mathrm{lca}(u,v)]$$

**为什么减两倍**：$u \to \text{root}$ 和 $v \to \text{root}$ 这两条路径在
LCA 上方**完全重合**，重合部分被算了两次，要减掉两次。

| 需求 | 公式 |
| --- | --- |
| 路径**边数**（无权） | $\mathrm{dep}[u]+\mathrm{dep}[v]-2\mathrm{dep}[l]$ |
| 路径**权值和**（带权） | $D[u]+D[v]-2D[l]$，$D$ 是根到该点的权和 |
| 路径**异或和** | $X[u] \oplus X[v]$（**不用减！**异或自己抵消，见 [Trie 字典树 §5](../../string/trie.md)） |
| 路径**点数** | 边数 $+1$ |
| 判 $w$ 是否在路径 $u\to v$ 上 | $\mathrm{dist}(u,w)+\mathrm{dist}(w,v) = \mathrm{dist}(u,v)$ |
| 路径的**中点** | 从深的那端向上跳 $\lfloor \mathrm{dist}/2 \rfloor$ 步（倍增求 $k$ 级祖先） |

**树上差分**：给路径 $u\to v$ 上所有点加 $k$，只在 4 个点打标记，最后一次子树求和：

| 类型 | 标记 |
| --- | --- |
| **点差分** | $d_u\mathrel{+}=k$，$d_v\mathrel{+}=k$，$d_{l}\mathrel{-}=k$，$d_{par(l)}\mathrel{-}=k$ |
| **边差分** | $d_u\mathrel{+}=k$，$d_v\mathrel{+}=k$，$d_{l}\mathrel{-}=2k$ |

收尾的「子树求和」正是 [`reversed(BFS 序)` 就是后序](basic.md#4-reversedbfs-序-就是后序)的一趟循环。
完整讨论见 [前缀和与差分 §6](../../basic/prefix-sum.md)。

---

---

## 2　最近公共祖先（LCA）

> **LCA$(u,v)$**：既是 $u$ 的祖先又是 $v$ 的祖先中**深度最大**的那个点。

三条主流路线，Python 下的取舍和 C++ **完全不同**。

### 路线一：倍增（通用首选）

$fa_j[v]$ = $v$ 向上跳 $2^j$ 步的祖先，$fa_j[v] = fa_{j-1}[fa_{j-1}[v]]$。

```python
def build_lca_lifting(n, start, adj, root):
    """倍增 LCA 预处理。O(n log n)。返回 (dep, fa, LOG, order)。

    0 号点当哨兵（fa[*][0] = 0），跳出树顶自动停在 0，查询里不用写边界判断。
    """
    LOG = max(1, n.bit_length())             # 跳 2^(LOG-1) 步已经超过树高，够用
    dep = [0] * (n + 1)                      # dep[0] = 0 是哨兵；根的深度设为 1
                                             # 根不取 0，是为了让 dep == 0 能当未访问标记
    fa = [[0] * (n + 1) for _ in range(LOG)]  # fa[j][v] = v 向上 2^j 步的祖先
    f0 = fa[0]                               # 第 0 层就是直接父亲
    dep[root] = 1
    order = [root]
    for u in order:                          # BFS 求深度与父亲，不用递归
        du = dep[u] + 1
        for i in range(start[u], start[u + 1]):
            v = adj[i]
            if dep[v] == 0:                  # dep 兼任访问标记
                dep[v] = du
                f0[v] = u
                order.append(v)
    for j in range(1, LOG):                  # 倍增递推：跳 2^j 步 = 连跳两次 2^(j-1) 步
        prev = fa[j - 1]
        fa[j] = [prev[prev[v]] for v in range(n + 1)]   # ★ 整层列表推导，C 层循环
                                             # 跳出树顶的点会落到 0，并一直停在 0
    return dep, fa, LOG, order


def lca_lifting(x, y, dep, fa, LOG):
    """倍增查询 LCA。O(log n)。"""
    if dep[x] < dep[y]:
        x, y = y, x                          # 统一成「x 更深」，后面只往上提 x
    d = dep[x] - dep[y]                      # 要提升的层数
    j = 0
    while d:                                 # ① 把深的那个提到同一层
        if d & 1:                            # d 的二进制第 j 位为 1 -> 跳 2^j 步
            x = fa[j][x]                     # 层差被拆成若干个 2 的幂，共跳 O(log n) 次
        d >>= 1
        j += 1
    if x == y:                               # ★ 必须先判：y 可能本来就是 x 的祖先
        return x
    for j in range(LOG - 1, -1, -1):         # ② 一起上跳：跳完仍不同才跳
        if fa[j][x] != fa[j][y]:             # 相等说明跳过头了（越过了 LCA），不跳
            x = fa[j][x]                     # 从大步长到小步长，逼近「最深的非公共祖先」
            y = fa[j][y]
    return fa[0][x]                          # 此时两者的父亲就是 LCA
```

> ⚠️ **第二个循环是「不同才跳」**。要找的是「最深的、仍然不是公共祖先的位置」；
> 若 $fa_j[x] = fa_j[y]$ 说明跳过头了。
> **写成 `if fa[j][x] == fa[j][y]: x = fa[j][x]` 是最常见的错法。**

> ⚠️ **`x == y` 一定要在第二个循环之前判**。若 $y$ 本来就是 $x$ 的祖先，
> 提到同层后两者已相等，此时进第二个循环会返回 `fa[0][x]`（多跳一层），答案偏浅。

倍增的通用讨论（快速幂、ST 表、序列倍增）见 [倍增](../../basic/binary-lifting.md)。

### 路线二：Tarjan 离线

**思想**：一遍 DFS，用并查集把「已经回溯完的子树」合并到父亲上。
DFS 到 $u$ 时，若询问 $(u,v)$ 的 $v$ 已经访问过，则 $\mathrm{lca} = \mathrm{find}(v)$。

```python
# [片段] Tarjan 离线 LCA 的骨架（需配迭代 DFS）
# 1) 把所有询问挂到两个端点上：qry[u].append((v, 询问编号))
# 2) 迭代 DFS：
#      进入 u：vis[u] = 1
#      离开 u 的每个孩子 v 之后：parent[v] = u   （并查集合并到父亲）
#      处理 u 时：对 qry[u] 里每个 (v, id)，若 vis[v]: ans[id] = find(v)
# 3) 关键点：合并必须发生在「孩子子树完全处理完」之后，
#    所以需要「进入 / 离开」两个时机 -> 事件栈式迭代 DFS（见 90.5 模板二）
```

| Tarjan 离线 | 评价 |
| --- | --- |
| 复杂度 | $O((n+q)\,\alpha(n))$，**理论最优** |
| 要求 | **必须离线**（所有询问预先给出） |
| Python 现实性 | ⚠️ 需要事件栈式迭代 DFS + 把 $q$ 个询问挂到点上，常数不小；$n,q \le 10^5$ 可行，$5\times10^5$ 很吃力 |
| 代码量 | 最大（迭代 DFS + 并查集 + 挂询问） |

### 路线三：欧拉序 + ST 表（**Python 下最快**）

**核心归约**：

> 对树做**欧拉序**（DFS 进入时记一次，每次从孩子回溯回来也记一次，长度恰好 $2n-1$），
> 则 $\mathrm{lca}(u,v) = $ 欧拉序区间 $[\mathrm{first}[u],\ \mathrm{first}[v]]$ 里**深度最小**的那个点。

**为什么**：从 $u$ 走到 $v$ 的这段欧拉序必然经过它们的 LCA（要出这棵子树只能从 LCA 走），
而且不会走到比 LCA 更浅的地方（那要先离开 LCA 的子树，与 $v$ 在子树内矛盾）。

于是 **LCA 变成了 RMQ**（Range Minimum Query，区间最值查询：给定数组和一个区间，
问区间内的最小值）。RMQ 可以用 **ST 表**（Sparse Table，稀疏表：预处理所有
「起点 $i$、长度 $2^j$」的区间最值）做到 $O(1)$ 查询，见
[倍增](../../basic/binary-lifting.md)。

**编码技巧**：把 $(\text{深度},\ \text{点号})$ 压进**一个整数** `dep << 20 | node`
（要求 $n < 2^{20} = 1048576$）。这样：

- 比较大小就是比较整数，**可以直接用内置 `min`**；
- ST 表建表能写成 `list(map(min, prev, prev[h:]))`，**整层比较全在 C 层**；
- 取到最小值后 `& 0xFFFFF` 就是 LCA 的点号。
- 区间里深度最小的点**唯一**（就是 LCA），所以不会有并列歧义。

```python
def build_lca_euler(n, start, adj, root, SH=20):
    """欧拉序 + ST 表 LCA。预处理 O(n log n)，查询 O(1)。

    欧拉序长度 2n-1；元素是 (dep << SH) | node，可直接用 min 比较。
    要求 n < 2^SH。迭代式 DFS，n = 5e5 也不会爆栈。
    """
    par = [0] * (n + 1)
    ptr = start[:]                           # 每个点扫到邻接表的哪里了
                                             # 这就是「手工保存的循环变量」，代替递归现场
    first = [0] * (n + 1)                    # first[u] = u 在欧拉序里首次出现的下标
    euler = []
    push = euler.append
    dep = 0                                  # 当前栈顶的深度，随进出栈同步升降
    stk = [root]
    first[root] = 0
    push(root)                               # (0 << SH) | root，根的深度是 0
    while stk:
        u = stk[-1]                          # 只看栈顶，不弹出：它的孩子可能还没走完
        p = ptr[u]
        if p < start[u + 1]:                 # u 还有没访问过的邻居
            ptr[u] = p + 1                   # 游标右移，下次从后一个邻居继续
            v = adj[p]
            if v != par[u]:                  # 树上不需要 vis，只要不走回父亲
                par[v] = u
                dep += 1
                first[v] = len(euler)        # 记下 v 首次出现的位置
                push((dep << SH) | v)
                stk.append(v)                # 下潜一层
        else:
            stk.pop()                        # u 的邻居扫完了，回溯
            dep -= 1
            if stk:
                push((dep << SH) | stk[-1])  # ★ 回溯到父亲，再记一次
                                             # 这一步让欧拉序长度成为 2n-1
    # ---- ST 表（Sparse Table，稀疏表）：st[j][i] = 从 i 开始 2^j 个元素的最小值 ----
    st = [euler]                             # 第 0 层就是欧拉序本身（区间长度 1）
    L = len(euler)
    j = 1
    while (1 << j) <= L:
        prev = st[-1]
        h = 1 << (j - 1)                     # 上一层的区间长度
        st.append(list(map(min, prev, prev[h:])))   # ★ 整层一次算完，全在 C 层
                                             # 两个错开 h 的半区间取 min 即得本层
        j += 1
    return first, st


def lca_euler(u, v, first, st, SH=20):
    """O(1) 查询 LCA。"""
    l = first[u]
    r = first[v]
    if l > r:
        l, r = r, l                          # 保证 l <= r，区间才有意义
    k = (r - l + 1).bit_length() - 1         # ⌊log2(len)⌋
    row = st[k]
    a = row[l]                               # 从左端起的 2^k 个
    b = row[r - (1 << k) + 1]                # 到右端为止的 2^k 个；两段重叠但不影响取 min
    return (a if a < b else b) & ((1 << SH) - 1)   # 低位掩码还原出点号
```

> **`list(map(min, prev, prev[h:]))` 是这条路线在 Python 下取胜的唯一原因**。
> `map` 遇到较短的可迭代对象就停止，正好得到长度 $L-2^j+1$ 的新层，
> **而整层的 $L$ 次比较全部在 C 层完成**。
> 手写 `for i in range(...)` 要慢 5–10 倍。同一个技巧见 [倍增 §2 ST 表](../../basic/binary-lifting.md)。

### 内存问题：$n$ 很大时 ST 表放不下

欧拉序长 $2n-1$。$n = 5\times10^5$ 时 $L \approx 10^6$，
ST 表有 $\lceil\log_2 L\rceil = 20$ 层，共 $2\times10^7$ 个元素——
**Python 的 `list` 存这些非缓存整数要 150 MB 以上，建表也要好几秒。**

**解法：分块 + 只对块间建 ST 表。**

| | 朴素 ST 表 | 分块 + 块间 ST 表 |
| --- | --- | --- |
| 块长 $B$ | 1 | **64** |
| 表的元素数 | $L\log L \approx 2\times10^7$ | $\dfrac{L}{B}\log\dfrac{L}{B} \approx 2\times10^5$（**降两个数量级**） |
| 查询 | 2 次表访问 | 两端零散部分 `min(切片)`（**C 层**扫 $\le 64$ 个）+ 中间整块查表 |
| 查询复杂度 | $O(1)$ | $O(B)$ 但常数极小（切片 `min` 在 C 层） |

这正是 BISHI124 题解采用的结构，完整代码见[倍增 §5](../../basic/binary-lifting.md)。

### 三条路线的对比

| | 倍增 | Tarjan 离线 | **欧拉序 + ST 表** |
| --- | --- | --- | --- |
| 预处理 | $O(n\log n)$ | $O(n\,\alpha)$ | $O(n\log n)$ |
| 单次查询 | $O(\log n)$ | 均摊 $O(\alpha)$ | **$O(1)$** |
| 在线？ | ✅ | ❌ 必须离线 | ✅ |
| 顺便能求 $k$ 级祖先 / 路径最值 | ✅ **只有倍增能** | ❌ | ❌ |
| 预处理的 Python 层操作量 | $n\log n$ 次（**列表推导，半 C 层**） | $O(n+q)$ 次（纯 Python） | $L$ 次 DFS + **建表全 C 层** |
| 查询的 Python 层操作量 | $q\log n$ 次（**纯 Python，最贵**） | $O(q\,\alpha)$ | **$q \times$ 常数** |
| 代码量 | 中 | 大 | 中 |
| **Python 推荐场景** | $n,q \le 2\times10^5$；或需要 $k$ 级祖先 / 路径最值 | 很少（常数不划算） | **$q$ 很大时唯一现实的路线** |

| 规模（$n \approx q$） | 倍增 | 欧拉序 + ST 表 |
| --- | --- | --- |
| $10^5$ | ✅ 约 1–2 s | ✅ 约 1 s |
| $2\times10^5$ | ⚠️ 约 3–4 s | ✅ 约 1.5–2 s |
| $5\times10^5$ | ❌ 建表 $10^7$ + 查询 $10^7$ 次 Python 层操作 | ⚠️ **仍然很险**（见 BISHI124） |

> **一句话决策**：
> **查询次数少（$q \le 10^5$）或需要「跳 $k$ 步」→ 倍增；
> 查询次数极大（$q \ge 3\times10^5$）→ 欧拉序 + 分块 ST 表。**
> Tarjan 在 C++ 里是最优解，在 Python 里几乎从不划算。

---

---

## 3　例题

<!-- CHAPTER-EXAMPLE-TABLE -->

### BISHI124 【模板】最近公共祖先（LCA）（中等）

> 给定 $N$ 个点、以 $R$ 为根的多叉树，$M$ 次询问两点的 LCA。
> $1 \le R \le N \le 5\times10^5$，$1 \le M \le 5\times10^5$。
> 树以 $N-1$ 条**无向**边 $(x,y)$ 给出（只表示相连，方向要靠 $R$ 定）。
> 时限：C/C++ 3 秒，**其他语言 6 秒**；空间：其他语言 512 MB。
> 题面见 [原题](https://www.nowcoder.com/practice/8004903f8eff4473b5c590b85afd7217)。
> 题解见 [`solutions/nowcoder/BISHI124/sol.py`](../../solutions/BISHI124.md)（已通过官方样例验证）。

#### 第一步：为什么不能用倍增

$N = M = 5\times10^5$，$\log_2 N = 19$：

| 阶段 | Python 层操作量 |
| --- | --- |
| 倍增建表 $19 \times 5\times10^5$ | $\approx 10^7$ 次（列表推导，约 3–5 s） |
| $5\times10^5$ 次查询 $\times$ 约 20 次跳跃 | $\approx 10^7$ 次（纯 Python 循环，约 8–12 s） |
| 内存：19 层 $\times$ $5\times10^5$ | $10^7$ 个列表槽，**约 80 MB 指针 + 整数对象** |

**总计 $2\times10^7$ 次 Python 层操作，时限只有 6 秒——必挂。**
[倍增](../../basic/binary-lifting.md) 给出的倍增模板在这个规模上确实过不去，
所以本章承担「替代路线」这部分。

#### 第二步：欧拉序 + 分块 ST 表

按 94.9 路线三：欧拉序把 LCA 归约成 RMQ，**查询降到 $O(1)$**；
再用「分块 + 块间 ST 表」把表的规模从 $2\times10^7$ 降到 $2\times10^5$。

```python
import sys


def main():
    data = sys.stdin.buffer.read().split()
    N = int(data[0]); M = int(data[1]); R = int(data[2])

    # ---- CSR 邻接表：deg 前缀和 + 一次填充（5e5 个小 list 的内存扛不住）----
    ne = 2 * (N - 1)
    es = list(map(int, data[3:3 + ne]))      # 只解析一次，别在两个循环里各 int() 一遍
    deg = [0] * (N + 2)
    for x in es:
        deg[x] += 1
    start = [0] * (N + 2)
    acc = 0
    for v in range(1, N + 1):
        start[v] = acc
        acc += deg[v]
    start[N + 1] = acc
    pos = start[:]
    adj = [0] * acc
    for i in range(0, ne, 2):
        x = es[i]; y = es[i + 1]
        adj[pos[x]] = y; pos[x] += 1
        adj[pos[y]] = x; pos[y] += 1

    # ---- 迭代式 DFS 生成欧拉序（元素 = dep << 20 | node）----
    par = [0] * (N + 1)
    ptr = start[:]                           # 每个点当前扫到邻接表的哪里
    euler = []
    push = euler.append
    first = [0] * (N + 1)
    dep = 0
    stk = [R]
    par[R] = 0
    first[R] = 0
    push(R)                                  # dep = 0
    while stk:
        u = stk[-1]
        p = ptr[u]
        if p < start[u + 1]:
            ptr[u] = p + 1
            v = adj[p]
            if v != par[u]:                  # 树上不需要 vis，不走回父亲即可
                par[v] = u
                dep += 1
                first[v] = len(euler)
                push((dep << 20) | v)
                stk.append(v)
        else:
            stk.pop()
            dep -= 1
            if stk:
                push((dep << 20) | stk[-1])  # 回溯，再记一次父亲

    L = len(euler)
    # ---- 分块 + 块间稀疏表：块长 64，表只有 14 * 1.6e4 ≈ 2e5 个元素 ----
    B = 64
    nb = (L + B - 1) // B
    blk = [min(euler[b * B:(b + 1) * B]) for b in range(nb)]   # 每块最小值，C 层
    st = [blk]
    j = 1
    while (1 << j) <= nb:
        prev = st[-1]
        h = 1 << (j - 1)
        st.append(list(map(min, prev, prev[h:])))              # ★ 整层 C 层建表
        j += 1

    p = 3 + ne
    out = []
    push = out.append
    MASK = (1 << 20) - 1
    for _ in range(M):
        a = int(data[p]); b = int(data[p + 1])
        p += 2
        l = first[a]; r = first[b]
        if l > r:
            l, r = r, l
        bl = l // B
        br = r // B
        if bl == br:                         # 同一块内：直接 C 层扫 <= 64 个
            v = min(euler[l:r + 1])
        else:
            v = min(euler[l:(bl + 1) * B])   # 左端零散部分
            w = min(euler[br * B:r + 1])     # 右端零散部分
            if w < v:
                v = w
            if br - bl > 1:                  # 中间的整块查稀疏表
                k = (br - bl - 1).bit_length() - 1
                row = st[k]
                x = row[bl + 1]
                y = row[br - (1 << k)]
                if x < v:
                    v = x
                if y < v:
                    v = y
        push(v & MASK)                       # 取回点号
    sys.stdout.write("\n".join(map(str, out)) + "\n")


main()
```

**复杂度**：预处理 $O(N)$（DFS + 分块）$+\ O(n_b\log n_b)$（块间 ST 表），
**查询 $O(1)$**（两次 C 层切片 `min` + 两次表访问）。

#### 第三步：诚实的可行性判断

> ⚠️ **本题在 CPython 3.9 下大概率 TLE**，即使用上了上面这套「理论最优」的做法：
>
> | 阶段 | Python 层操作量 |
> | --- | --- |
> | 读入 $2\times5\times10^5 + 2\times5\times10^5 = 2\times10^6$ 个 token 并 `int()` | $\ge 1$ s |
> | 建 CSR（度数 + 前缀和 + 填充） | $\approx 2\times10^6$ 次 |
> | 迭代 DFS 生成欧拉序（$10^6$ 个元素，每个要 push / 判父亲） | $\approx 1.5\times10^6$ 次 |
> | $5\times10^5$ 次查询 $\times$（约 10 次 Python 层操作 + 2 次 C 层切片 `min`） | $\approx 5\times10^6$ 次 |
>
> 总量约 $6\times10^6 \sim 8\times10^6$ 次 Python 层操作，**实测在 8–15 秒量级**，
> 而时限是「其他语言 6 秒」。
>
> **这属于「规模对 Python 不友好」，而不是做法有问题**——
> 预处理 $O(N)$ + 查询 $O(1)$ 已经是理论最优，没有更好的算法了。
> 换 PyPy 可过；CPython 下这题只能接受。

**这题给出的三条判据**：

| 判据 | 内容 |
| --- | --- |
| **算法选择** | $q$ 很大时，**把「查询」的复杂度压到 $O(1)$ 比压预处理更重要**。倍增的 $q\log n$ 全是纯 Python 循环，是本题的绝对瓶颈 |
| **把循环下沉到 C 层** | `list(map(min, prev, prev[h:]))` 建表、`min(切片)` 查零散部分、`list(map(int, ...))` 解析——**能交给 C 的就一个字节都不留在 Python 里** |
| **内存也要算** | 朴素 ST 表 $2\times10^7$ 个元素在 512 MB 下必 MLE；**分块把它降两个数量级**。「$O(1)$ 查询」在 Python 里必须配「小表」才成立 |

**四个实现坑**：

1. **树是无根边给出的**（$x\ y$ 只表示相连），根 $R$ 单独给出。
   **必须迭代式 DFS**——递归深度可达 $5\times10^5$；
2. **欧拉序长度是 $2N-1$**，`first[]` 记**第一次**出现的位置。
   写成「最后一次」也能对，但混用就错；
3. **查询时若 `first[u] > first[v]` 要交换**；$u = v$ 时区间退化成一个点，答案是自己，仍然正确；
4. **编码位宽**：$N \le 5\times10^5 < 2^{20}$，所以 `dep << 20 | node` 安全。
   若 $N$ 能到 $2\times10^6$，位宽要改成 21——**改位宽时 `MASK` 要同步改**。

> **本题也是 [倍增](../../basic/binary-lifting.md) 的例题**。
> 分工是：[倍增](../../basic/binary-lifting.md)负责倍增模板本身（并诚实标注它在这个规模上过不去），
> 本章负责「替代路线 + 为什么」。**同一道题，两种算法，两层理解。**

---

---

### 面试题单里的两道 LCA 题

[BM37](../../solutions/BM37.md)与[BM38](../../solutions/BM38.md)
是同一个问题的两种前提，值得放在一起看——**前提变了，最优做法就变。**

**BM37 给的是二叉搜索树**，于是根本不需要 §2 的任何模板：
从根往下走，若两个目标值都小于当前节点就往左，都大于就往右，
否则当前节点就是答案（一个在左、一个在右，或者其中之一正是当前节点）。
一次下降 $O(h)$，不用预处理、不用额外空间。**有序性把问题降了一个量级。**

**BM38 是一般二叉树**，有序性没了，只能回到通用办法。
数据规模在 $10^2$ 量级时，最省事的是各求一次「根到目标节点的路径」，
再比较两条路径的最长公共前缀，$O(n)$ 时间、$O(h)$ 空间。
查询次数一多就该换成 §2 的倍增或欧拉序 ＋ ST 表——
**判断标准是查询次数**：单次查询用暴力，多次查询才值得付预处理的代价。

### LC236 二叉树的最近公共祖先

[LC236](../../solutions/LC236.md)与本章的模板题不在一个量级上：
它只问**一次**查询，树是二叉树，节点数在 $10^5$ 以内。
一次查询用不着倍增或 ST 表那套 $O(n \log n)$ 的预处理，一遍后序遍历就够——
某节点的左右子树各命中一个目标，它就是答案；只命中一个就把那一侧的结果原样上传；
一个都没命中则上传空。整体 $O(n)$ 时间、$O(H)$ 空间。
**预处理只有在查询次数够多时才划算**：$q$ 次查询下逐次遍历是 $O(qn)$，
倍增是 $O(n \log n + q \log n)$，分界点大致落在 $q$ 与 $\log n$ 同阶的地方。
这棵树的深度可能达到 $10^5$，递归写法同样要换成显式栈。

## 4　本章速查

### 路径

| 要点 | 结论 |
| --- | --- |
| 路径边数 | $\mathrm{dep}[u]+\mathrm{dep}[v]-2\mathrm{dep}[l]$ |
| 路径权和 | $D[u]+D[v]-2D[l]$ |
| 路径**异或和** | $X[u]\oplus X[v]$，**不用减** |
| 判 $w$ 在路径上 | $\mathrm{dist}(u,w)+\mathrm{dist}(w,v)=\mathrm{dist}(u,v)$ |
| 树上点差分 | $+k,+k$ 于 $u,v$；$-k$ 于 $l$；$-k$ 于 $par(l)$ |
| 树上边差分 | $+k,+k$ 于 $u,v$；$\mathbf{-2k}$ 于 $l$ |

### LCA

| 要点 | 结论 |
| --- | --- |
| 倍增表 | $fa_j[v]=fa_{j-1}[fa_{j-1}[v]]$；**整层列表推导建表** |
| 倍增查询 ① | 先把深的提到同层 |
| 倍增查询 ② | **`fa[j][x] != fa[j][y]` 才跳**（跳完仍不同才安全） |
| ⚠️ `x == y` | **必须在第二个循环前判**，否则答案偏浅 |
| 0 号点哨兵 | `fa[*][0] = 0`，跳出树顶自动停住 |
| **欧拉序归约** | $\mathrm{lca}(u,v)=$ 欧拉序 $[\mathrm{first}_u,\mathrm{first}_v]$ 里**深度最小**的点 |
| 编码技巧 | `dep << 20 \| node`，**直接用内置 `min` 比较**（要求 $n<2^{20}$） |
| ST 表建表 | **`list(map(min, prev, prev[h:]))`** —— 整层在 C 层 |
| $n$ 大时的内存 | 朴素 ST 表 $2\times10^7$ 元素必 MLE ⟹ **分块（$B=64$）+ 块间 ST 表** |
| Tarjan 离线 | 理论最优 $O((n+q)\alpha)$，但**必须离线**且 Python 常数不划算 |
| 只有倍增能做 | $k$ 级祖先、路径最值（次小生成树用的就是它） |
| **选型** | $q \le 10^5$ 或要跳 $k$ 步 → **倍增**；$q \ge 3\times10^5$ → **欧拉序 + 分块 ST 表** |

| 规模 | Python 现实性 |
| --- | --- |
| 遍历 / BFS 序倒序，$n \le 5\times10^5$ | ✅ 纯数组循环 |
| DFS 序 + 树状数组（子树改子树查），$n \le 2\times10^5$ | ✅ |
| 直径（两次 BFS），$n \le 5\times10^5$ | ✅ |
| 重心，$n \le 5\times10^5$ | ✅ 一遍 `sz` + 一遍扫边 |
| LCA 倍增，$n,q \le 2\times10^5$ | ⚠️ 约 3–4 s |
| LCA 倍增，$n,q = 5\times10^5$ | ❌ $2\times10^7$ 次 Python 层操作 |
| **LCA 欧拉序 + 分块 ST 表，$n,q = 5\times10^5$** | ⚠️ **8–15 s vs 6 s 时限，极险**（BISHI124；PyPy 可过） |
| 树链剖分（线段树），$n \le 10^5$ | ⚠️ 见 [树链剖分](hld.md) |
| 点分治，$n \le 5\times10^4$ | ⚠️ $O(n\log n)$ 但常数大 |

| 看到什么 → 想到什么 |
| --- |
| 「$n-1$ 条边 + 连通」 | 是树；很多图论算法可以简化 |
| 「输出先序/中序/后序」 | 三个迭代模板（BISHI96） |
| 「求子树的和 / 子树整体修改」 | **DFS 序 + 树状数组** |
| 「先算儿子再算父亲」 | **`reversed(BFS 序)`** |
| 「树上最长路径」 | 直径：两次 BFS（非负权）/ 树形 DP（可负权） |
| 「删一个点使最大块最小」 | **重心** |
| 「使到所有点距离和最小」 | 重心 |
| 「使到最远点距离最小」 | **中心** = 直径中点 |
| 「多次询问两点距离 / 祖先」 | **LCA**（BISHI124） |
| 「跳 $k$ 级祖先 / 路径最大边」 | **只能倍增** |
| 「路径上所有点加 $k$，最后查每点」 | **树上差分**（[前缀和与差分](../../basic/prefix-sum.md)） |
| 「路径修改 + 路径查询」 | **树链剖分**（[树链剖分](hld.md)） |
| 「树上路径异或最大」 | 前缀异或 + 01-Trie（[Trie 字典树](../../string/trie.md)） |

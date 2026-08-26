# 附录 B　Python 算法模板速查

> 本附录按 NOIP 复赛算法模板清单的通行组织方式，把全书模板汇总成一处。
> 所有代码兼容 **Python 3.9**。每个模板都注明了**详细讲解所在章节**与**Python 下的可行规模**。
>
> 需要完整推导、正确性证明与踩坑记录时，请回到对应章节——这里只放能直接抄的部分。

---

## B.0　通用开头

```python
import sys
from collections import deque, defaultdict, Counter
from heapq import heappush, heappop, heapify
from bisect import bisect_left, bisect_right, insort
from itertools import accumulate, permutations, combinations
from math import gcd, isqrt, inf
from functools import lru_cache, cmp_to_key


def main():
    data = sys.stdin.buffer.read().split()
    p = 0
    n = int(data[p]); p += 1
    ...
    sys.stdout.write("\n".join(map(str, out)) + "\n")


main()
```

> 三条铁律：**逻辑装进 `main()`**（快 20–30%）、**读用 `buffer.read().split()`**、
> **写用 `"\n".join()`**。详见 [输入输出处理](../toolkit/io.md)。
>
> 递归深度：
> ```python
> import threading
> sys.setrecursionlimit(1 << 20)
> threading.stack_size(1 << 26)      # 64 MB；只调 setrecursionlimit 仍会爆 C 栈
> t = threading.Thread(target=main); t.start(); t.join()
> ```

---

## B.1　高精度

Python 原生 `int` 无上限，**四则运算直接用 `+ - * // %`，不需要模板**。
详见 [高精度与大整数](../toolkit/bignum.md)。

| 需求 | 写法 |
| --- | --- |
| 精确阶乘 | `math.factorial(n)` |
| 幂取模 | `pow(a, b, m)` ← C 实现，别手写 |
| 整数开方 | `math.isqrt(n)` ← 别用 `n ** 0.5` |
| 精确小数 | `decimal.Decimal(字符串)` |
| 精确分数 | `fractions.Fraction` |

> **唯一要小心的是性能**：循环里连乘必须每步取模，否则大整数膨胀。

---

## B.2　排序

实战一律用内置 `sorted`（Timsort，C 实现）。手写只有教学意义。
详见 [排序](../basic/sorting.md)、[自定义排序](../python/sorting.md)。

```python
# 多关键字：第一维升、第二维降
a.sort(key=lambda x: (x[0], -x[1]))

# 无法取负时（如字符串降序 + 数字升序）：两趟稳定排序，后排的是主关键字
a.sort(key=lambda x: x[1])                 # 次关键字
a.sort(key=lambda x: x[0], reverse=True)   # 主关键字

# 实在不行才用 cmp_to_key（慢 8–15 倍）
from functools import cmp_to_key
a.sort(key=cmp_to_key(lambda x, y: -1 if ... else 1))
```

### 归并排序求逆序对

```python
def count_inv(a):
    """归并排序统计逆序对数，O(n log n)。"""
    def rec(lo, hi):
        if hi - lo <= 1:
            return 0
        mid = (lo + hi) // 2
        cnt = rec(lo, mid) + rec(mid, hi)
        left, right = a[lo:mid], a[mid:hi]
        i = j = 0
        k = lo
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                a[k] = left[i]; i += 1
            else:
                a[k] = right[j]; j += 1
                cnt += len(left) - i          # left[i:] 都比 right[j] 大
            k += 1
        while i < len(left):
            a[k] = left[i]; i += 1; k += 1
        while j < len(right):
            a[k] = right[j]; j += 1; k += 1
        return cnt
    return rec(0, len(a))
```

> 递归深度只有 $O(\log n)$，Python 里安全。$n = 10^5$ 实测 0.16 秒，
> 与「离散化 + 树状数组」打成平手。

### 离散化

```python
vals = sorted(set(a))
rank = {v: i for i, v in enumerate(vals)}      # 值 -> 排名
b = [rank[x] for x in a]
# 反查：vals[r]
```

---

## B.3　二分

详见 [二分](../basic/binary-search.md)。

```python
# 优先用内置（C 实现）
bisect_left(a, x)      # 第一个 >= x 的下标
bisect_right(a, x)     # 第一个  > x 的下标
# 3.9 不支持 key= 参数（3.10 才加），需要时预先构造键数组

# 手写：找第一个满足 check 的位置（check 单调 False->True）
lo, hi = 0, n                     # 半开区间 [lo, hi)
while lo < hi:
    mid = (lo + hi) // 2
    if check(mid):
        hi = mid
    else:
        lo = mid + 1
# lo 就是答案；若不存在则 lo == n
```

### 二分答案

```python
lo, hi = 最小可能, 最大可能
while lo < hi:
    mid = (lo + hi) // 2
    if feasible(mid):
        hi = mid                  # 求最小可行值
    else:
        lo = mid + 1
```

### 实数二分：用固定次数，不要用 eps

```python
lo, hi = 0.0, 1e18
for _ in range(100):              # 2^-100 倍精度，绝不死循环
    mid = (lo + hi) / 2
    if check(mid):
        hi = mid
    else:
        lo = mid
print("%.6f" % lo)
```

### 三分（求单峰极值）

```python
lo, hi = 0.0, 1e9
for _ in range(200):
    m1 = lo + (hi - lo) / 3
    m2 = hi - (hi - lo) / 3
    if f(m1) < f(m2):             # 求最大值
        lo = m1
    else:
        hi = m2
```

---

## B.4　前缀和与差分

详见 [前缀和与差分](../basic/prefix-sum.md)。

```python
# 一维前缀和：C 层
S = [0] + list(accumulate(a))     # S[i] = a[0]+...+a[i-1]
区间和(l, r) = S[r + 1] - S[l]    # 0-indexed 闭区间

# 一维差分：区间加
d = [0] * (n + 2)
d[l] += v; d[r + 1] -= v          # 对 [l, r] 加 v
a = list(accumulate(d))           # 还原

# 二维前缀和
S = [[0] * (m + 1) for _ in range(n + 1)]
for i in range(n):
    row, prev = a[i], S[i]
    cur = S[i + 1]
    s = 0
    for j in range(m):
        s += row[j]
        cur[j + 1] = prev[j + 1] + s
# 矩形和 (x1,y1)-(x2,y2)：S[x2+1][y2+1]-S[x1][y2+1]-S[x2+1][y1]+S[x1][y1]

# 二维差分：矩形加 v
d[x1][y1] += v; d[x1][y2+1] -= v; d[x2+1][y1] -= v; d[x2+1][y2+1] += v
```

---

## B.5　栈与队列

详见 [栈](../ds/stack.md)、[队列与双端队列](../ds/queue.md)。

```python
# 栈：直接用 list（append / pop 都是 O(1)）
st = []; st.append(x); st.pop()

# 队列：必须用 deque —— list.pop(0) 是 O(n)！
q = deque([start]); q.append(x); q.popleft()

# 队列的更快替代（只入队一次时）：list + 头指针
q, head = [start], 0
while head < len(q):
    u = q[head]; head += 1
    q.append(v)
```

### 单调栈：求左/右第一个更大（更小）元素

```python
def next_greater(a):
    """返回 res，res[i] 是右边第一个 > a[i] 的下标，无则 n。"""
    n = len(a)
    res = [n] * n
    st = []
    for i, x in enumerate(a):
        while st and a[st[-1]] < x:      # 求「>= 」时改 <=
            res[st.pop()] = i
        st.append(i)
    return res
```

### 单调队列：滑动窗口最值

```python
def sliding_max(a, k):
    dq, out = deque(), []
    for i, x in enumerate(a):
        while dq and dq[0] <= i - k:
            dq.popleft()                # 先弹过期
        while dq and a[dq[-1]] <= x:
            dq.pop()                    # 再维护单调
        dq.append(i)
        if i >= k - 1:
            out.append(a[dq[0]])
    return out
```

> **三步顺序**：弹队首过期 → 维护队尾单调 → 取答案。存**下标**不存值。
> 详见 [单调队列](../ds/monotonic-queue.md)。

---

## B.6　并查集

详见 [并查集](../ds/dsu.md)。

```python
class DSU:
    """迭代路径压缩 + 按大小合并，均摊 O(α(n))。"""

    def __init__(self, n):
        self.fa = list(range(n))
        self.sz = [1] * n

    def find(self, x):
        fa = self.fa
        root = x
        while fa[root] != root:
            root = fa[root]
        while fa[x] != root:            # 第二趟压缩
            fa[x], x = root, fa[x]
        return root

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.sz[ra] < self.sz[rb]:
            ra, rb = rb, ra
        self.fa[rb] = ra
        self.sz[ra] += self.sz[rb]
        return True
```

> **必须迭代**：递归 `find` 在链状数据下深度到 $n$，会爆栈。
> 扩展域并查集（处理「敌人的敌人是朋友」）：开 $2n$ 个点，$i$ 与 $i+n$ 表示两种阵营。

---

## B.7　堆与优先队列

详见 [优先队列与堆](../ds/heap.md)。

```python
h = []
heappush(h, x); heappop(h); h[0]        # 小根堆；h[0] 看堆顶是 O(1)
heapify(a)                              # 原地建堆，O(n) 不是 O(n log n)

# 大根堆：取负
heappush(h, -x); -heappop(h)

# 存元组时插一个唯一序号，防止比较到不可比较的对象
heappush(h, (dist, idx, obj))
```

### 堆 + 懒删除（模拟可删除堆）

```python
class LazyHeap:
    def __init__(self):
        self.h = []
        self.dead = Counter()
        self.n = 0

    def push(self, x):
        heappush(self.h, x); self.n += 1

    def erase(self, x):
        self.dead[x] += 1; self.n -= 1

    def top(self):
        while self.h and self.dead[self.h[0]]:
            self.dead[self.h[0]] -= 1
            heappop(self.h)
        return self.h[0] if self.h else None
```

### 反悔贪心两式

```python
# 容量型：选满 k 个后，新来的若更优就换掉最差的
if len(h) < k:
    heappush(h, x)
elif x > h[0]:
    heappushpop(h, x)

# 超限型（如「建筑抢修」）：先都选上，超限就退掉代价最大的
heappush(h, -cost); cur += cost
while cur > limit:
    cur += heappop(h)                   # 弹出的是 -最大代价
```

---

## B.8　树状数组与线段树

详见 [树状数组](../ds/fenwick.md) 与 [线段树](../ds/segment-tree.md)。

```python
class BIT:
    """单点加 + 前缀和查询，O(log n)。下标 1..n。"""

    def __init__(self, n):
        self.n = n
        self.t = [0] * (n + 1)

    def add(self, i, v):
        t, n = self.t, self.n
        while i <= n:
            t[i] += v
            i += i & (-i)

    def query(self, i):
        """前缀和 [1, i]。"""
        t, s = self.t, 0
        while i > 0:
            s += t[i]
            i -= i & (-i)
        return s

    def range_sum(self, l, r):
        return self.query(r) - self.query(l - 1)

    def kth(self, k):
        """求第 k 小（树状数组上倍增），要求 t 存的是计数。"""
        pos, n = 0, self.n
        step = 1 << (n.bit_length())
        while step:
            nxt = pos + step
            if nxt <= n and self.t[nxt] < k:
                pos = nxt
                k -= self.t[nxt]
            step >>= 1
        return pos + 1
```

> **能用树状数组就别用线段树**：常数小 5 倍，代码短一半。
> 「区间加 + 区间和」可用两个树状数组做差分实现，不必上线段树。

### 非递归线段树（区间加 + 区间和）

递归版在 Python 里常数极大，$n = q = 10^5$ 就很险。若必须用线段树，写非递归版；
完整实现（`LazySeg`）见 [线段树](../ds/segment-tree.md)。

### ST 表（静态区间最值）

```python
def build_st(a):
    """O(n log n) 建表，查询 O(1)。建表用 map 走 C 层。"""
    st = [a[:]]
    k, half = 1, 1
    while half * 2 <= len(a):
        prev = st[-1]
        st.append(list(map(max, prev, prev[half:])))
        half *= 2
    return st


def query_st(st, l, r):
    """闭区间 [l, r] 的最大值。"""
    k = (r - l + 1).bit_length() - 1
    row = st[k]
    return max(row[l], row[r - (1 << k) + 1])
```

---

## B.9　有序集合的替代方案

**Python 没有 `std::set`，且判题机没装 `sortedcontainers`。**
详见 [集合与多重集合](../ds/multiset.md)、
[平衡树与有序集合](../ds/balanced-tree.md)。

| 需求 | 方案 | 复杂度 |
| --- | --- | --- |
| 判存在、插入、删除 | `set` / `dict` | $O(1)$ |
| 计数（可重） | `Counter` | $O(1)$ |
| **前驱 / 后继**，值域 $\le 10^6$ | **两级值域位图** | $O(1)$ ← 最快 |
| 前驱 / 后继 / 第 $k$ 小，值域大 | 离散化 + 树状数组 + 倍增 | $O(\log n)$ |
| 只需最值 + 删除 | 堆 + 懒删除 | $O(\log n)$ |
| 可以离线 | 排序 + `bisect` | $O(n\log n)$ 总 |

```python
# 两级值域位图：核心思想（完整实现见「集合与多重集合」一章的 ValueSet）
BITS = 1024                          # 每块 1024 个值
# blocks[b] 是一个 1024 位的大整数位图；summary 标记哪些块非空
# 前驱：本块内 v & ((1<<r)-1) 取最高位；本块没有就去 summary 找相邻非空块
# 全程只做几次大整数位运算，都在 C 层
```

---

## B.10　字符串

详见 [字符串处理](../string/basic.md) ~ [Trie字典树](../string/trie.md)。

### KMP 前缀函数

```python
def prefix_function(s):
    """pi[i] = s[:i+1] 的最长真前缀=真后缀长度。均摊 O(n)。"""
    n = len(s)
    pi = [0] * n
    k = 0
    for i in range(1, n):
        while k and s[i] != s[k]:
            k = pi[k - 1]
        if s[i] == s[k]:
            k += 1
        pi[i] = k
    return pi
```

> **匹配本身优先用 `str.find` / `in`**（C 实现，通常更快）。
> KMP 的不可替代之处在于**求周期与 border**：
> 最小周期 $= n - \pi[n-1]$（当 $n \bmod (n-\pi[n-1]) = 0$ 时成立）。

### Manacher（最长回文子串）

```python
def manacher(s):
    """返回 d1, d2：以 i 为中心的奇/偶长回文半径。O(n)。"""
    n = len(s)
    d1 = [0] * n
    l, r = 0, -1
    for i in range(n):
        k = 1 if i > r else min(d1[l + r - i], r - i + 1)
        while i - k >= 0 and i + k < n and s[i - k] == s[i + k]:
            k += 1
        d1[i] = k
        if i + k - 1 > r:
            l, r = i - k + 1, i + k - 1
    d2 = [0] * n
    l, r = 0, -1
    for i in range(n):
        k = 0 if i > r else min(d2[l + r - i + 1], r - i + 1)
        while i - k - 1 >= 0 and i + k < n and s[i - k - 1] == s[i + k]:
            k += 1
        d2[i] = k
        if i + k - 1 > r:
            l, r = i - k, i + k - 1
    return d1, d2
```

### 字符串哈希

```python
MOD = (1 << 61) - 1                  # 大质数，单模够用
BASE = 131

def build_hash(s):
    n = len(s)
    h = [0] * (n + 1)
    pw = [1] * (n + 1)
    for i, c in enumerate(s):
        h[i + 1] = (h[i] * BASE + ord(c)) % MOD
        pw[i + 1] = pw[i] * BASE % MOD
    return h, pw


def sub_hash(h, pw, l, r):
    """闭区间 [l, r] 的哈希值。"""
    return (h[r + 1] - h[l] * pw[r - l + 1]) % MOD
```

> 防卡：把字符先过一个混淆函数（如 `ord(c) * 0x9E3779B1 & 0xFFFFFFFF`），
> 或用双模哈希。详见 [字符串哈希](../string/hash.md)。

### Trie（扁平 dict 版，Python 下最实用）

```python
class Trie:
    """单个扁平 dict，key = node * 128 + 字节值。比嵌套 dict 快、比数组省内存。"""

    def __init__(self):
        self.ch = {}
        self.cnt = [0]                # 经过每个节点的串数

    def insert(self, s):
        node = 0
        ch, cnt = self.ch, self.cnt
        for b in s:
            key = node * 128 + b
            nxt = ch.get(key)
            if nxt is None:
                nxt = len(cnt)
                ch[key] = nxt
                cnt.append(0)
            node = nxt
            cnt[node] += 1

    def count_prefix(self, s):
        node = 0
        ch = self.ch
        for b in s:
            node = ch.get(node * 128 + b)
            if node is None:
                return 0
        return self.cnt[node]
```

---

## B.11　搜索

详见 [DFS](../search/dfs.md) ~ [记忆化](../search/memoization.md)。

```python
# 网格 BFS
DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))
dist = [[-1] * m for _ in range(n)]
q = deque([(sx, sy)]); dist[sx][sy] = 0
while q:
    x, y = q.popleft()
    for dx, dy in DIRS:
        nx, ny = x + dx, y + dy
        if 0 <= nx < n and 0 <= ny < m and dist[nx][ny] < 0 and g[nx][ny] != '#':
            dist[nx][ny] = dist[x][y] + 1
            q.append((nx, ny))

# 0-1 BFS（边权只有 0 和 1）：deque 两端插入替代 Dijkstra
if w == 0:
    q.appendleft(v)
else:
    q.append(v)

# 迭代式 DFS（避免递归深度问题）
st = [start]
vis = bytearray(n)
vis[start] = 1
while st:
    u = st.pop()
    for v in g[u]:
        if not vis[v]:
            vis[v] = 1              # 入栈即标记，防重复入栈
            st.append(v)

# 回溯模板（排列）
def backtrack(path, used):
    if len(path) == n:
        out.append(path[:]); return
    for i in range(n):
        if not used[i]:
            used[i] = True; path.append(a[i])
            backtrack(path, used)
            path.pop(); used[i] = False
```

> 全排列直接用 `itertools.permutations`（C 实现），比手写回溯快很多。

---

## B.12　图论

详见 [图的表示与遍历](../graph/basic.md) ~ [树的基础与遍历](../graph/tree/basic.md)。

### 邻接表：定长 list of list 或 CSR

```python
# 别用 defaultdict(list) —— 大图下慢
g = [[] for _ in range(n + 1)]
for _ in range(m):
    u, v, w = ...
    g[u].append((v, w))
    g[v].append((u, w))

# CSR（更快，缓存友好）：先数度数再填
deg = [0] * (n + 1)
for u, v, w in edges:
    deg[u] += 1; deg[v] += 1
start = [0] * (n + 2)
for i in range(1, n + 1):
    start[i + 1] = start[i] + deg[i]
```

### Dijkstra（堆优化 + 懒删除）

```python
def dijkstra(n, g, s):
    dist = [inf] * (n + 1)
    dist[s] = 0
    h = [(0, s)]
    while h:
        d, u = heappop(h)
        if d > dist[u]:               # 懒删除：过期条目直接跳过
            continue
        for v, w in g[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heappush(h, (nd, v))
    return dist
```

> **无权图最短路用 BFS，不要上 Dijkstra**。边权只有 0/1 用 0-1 BFS。
> 负权边用 Bellman-Ford / SPFA；SPFA 在 Python 里常数大，能用 Dijkstra 就别用。

### Kruskal 最小生成树

```python
def kruskal(n, edges):
    """edges: [(w, u, v), ...]。返回 (总权值, 是否连通)。"""
    edges.sort()
    d = DSU(n + 1)
    total = cnt = 0
    for w, u, v in edges:
        if d.union(u, v):
            total += w
            cnt += 1
            if cnt == n - 1:
                break
    return total, cnt == n - 1
```

### 拓扑排序（Kahn）

```python
def topo_sort(n, g, indeg):
    q = [u for u in range(1, n + 1) if indeg[u] == 0]
    order, head = q[:], 0
    while head < len(order):
        u = order[head]; head += 1
        for v in g[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                order.append(v)
    return order if len(order) == n else None      # None 表示有环
```

> 字典序最小的拓扑序：把 `q` 换成堆。

### 二分图判定（BFS 染色）

```python
def is_bipartite(n, g):
    color = [-1] * (n + 1)
    for s in range(1, n + 1):         # 图可能不连通，每个点都要试
        if color[s] >= 0:
            continue
        color[s] = 0
        q = deque([s])
        while q:
            u = q.popleft()
            for v in g[u]:
                if color[v] < 0:
                    color[v] = color[u] ^ 1
                    q.append(v)
                elif color[v] == color[u]:
                    return False
    return True
```

### LCA 倍增

```python
def build_lca(n, g, root):
    LOG = max(1, n.bit_length())
    dep = [0] * (n + 1)
    up = [[0] * (n + 1) for _ in range(LOG)]
    order, head = [root], 0
    up[0][root] = root
    vis = bytearray(n + 1); vis[root] = 1
    while head < len(order):          # BFS 求深度与父亲
        u = order[head]; head += 1
        for v in g[u]:
            if not vis[v]:
                vis[v] = 1
                dep[v] = dep[u] + 1
                up[0][v] = u
                order.append(v)
    for k in range(1, LOG):
        prev, cur = up[k - 1], up[k]
        for v in range(1, n + 1):
            cur[v] = prev[prev[v]]
    return dep, up, LOG


def lca(u, v, dep, up, LOG):
    if dep[u] < dep[v]:
        u, v = v, u
    diff = dep[u] - dep[v]
    for k in range(LOG):
        if diff >> k & 1:
            u = up[k][u]
    if u == v:
        return u
    for k in range(LOG - 1, -1, -1):
        if up[k][u] != up[k][v]:
            u, v = up[k][u], up[k][v]
    return up[0][u]
```

> ⚠️ $N, M \le 5\times10^5$ 时倍增在 CPython 下会 TLE（建表 + 查询各约 $10^7$ 次 Python 操作）。
> 替代路线是「欧拉序 + 分块 + 块间 ST 表」，见 [LCA 与树上路径](../graph/tree/lca.md)。

---

## B.13　数论

详见 [数论基础](../math/number/basic.md) ~ [组合数学](../math/combi/basic.md)。

```python
# gcd / lcm（3.9 起 gcd 支持多参数，lcm 也是 3.9 引入）
gcd(a, b, c)
lcm = a // gcd(a, b) * b              # 先除后乘

# 幂取模：内置，别手写
pow(a, b, m)

# 模逆元
pow(a, m - 2, m)                      # m 为质数（费马小定理）
pow(a, -1, m)                         # 3.8+，要求 gcd(a, m) == 1，否则 ValueError
```

### 埃氏筛（bytearray + 切片步长赋值）

```python
def sieve(n):
    """返回 is_prime 的 bytearray。内层循环全在 C 层。"""
    is_p = bytearray([1]) * (n + 1)
    is_p[0:2] = b"\x00\x00"
    for i in range(2, isqrt(n) + 1):
        if is_p[i]:
            step = len(range(i * i, n + 1, i))
            is_p[i * i::i] = bytearray(step)
    return is_p
```

> **切片步长赋值是关键**：把「标记 $i$ 的所有倍数」这个 $O(n/i)$ 循环整个交给 C。
> $n = 10^7$ 可行；用 `list` 而不是 `bytearray` 会多占 8 倍内存。

### 欧拉线性筛（同时求 φ）

```python
def linear_sieve(n):
    phi = list(range(n + 1))
    primes = []
    is_c = bytearray(n + 1)
    for i in range(2, n + 1):
        if not is_c[i]:
            primes.append(i)
            phi[i] = i - 1
        for p in primes:
            if i * p > n:
                break
            is_c[i * p] = 1
            if i % p == 0:
                phi[i * p] = phi[i] * p
                break
            phi[i * p] = phi[i] * (p - 1)
    return primes, phi
```

### 质因数分解与判素数

```python
def factorize(n):
    """试除法，O(√n)。"""
    res = []
    for p in (2, 3):
        while n % p == 0:
            res.append(p); n //= p
    p = 5
    while p * p <= n:
        for d in (p, p + 2):          # 6k±1
            while n % d == 0:
                res.append(d); n //= d
        p += 6
    if n > 1:
        res.append(n)
    return res


def is_prime(n):
    """确定性 Miller-Rabin，对 n < 3.3e24 正确。"""
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % p == 0:
            return n == p
    d, r = n - 1, 0
    while d % 2 == 0:
        d //= 2; r += 1
    for a in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True
```

### 扩展欧几里得与线性同余方程

```python
def exgcd(a, b):
    """返回 (g, x, y) 满足 a*x + b*y = g = gcd(a, b)。迭代版，无递归深度风险。"""
    x0, x1, y0, y1 = 1, 0, 0, 1
    while b:
        q, a, b = a // b, b, a % b
        x0, x1 = x1, x0 - q * x1
        y0, y1 = y1, y0 - q * y1
    return a, x0, y0


def mod_inverse(a, m):
    """非质模数下的逆元；不存在返回 None。"""
    g, x, _ = exgcd(a % m, m)
    return None if g != 1 else x % m
```

### 组合数取模（预处理阶乘 + 逆元倒推）

```python
def build_comb(n, mod):
    """O(n) 预处理，之后 O(1) 查询。只做一次模幂。"""
    fac = [1] * (n + 1)
    for i in range(1, n + 1):
        fac[i] = fac[i - 1] * i % mod
    inv = [1] * (n + 1)
    inv[n] = pow(fac[n], mod - 2, mod)            # 唯一的一次模幂
    for i in range(n, 0, -1):
        inv[i - 1] = inv[i] * i % mod
    return fac, inv


def C(n, k, fac, inv, mod):
    if k < 0 or k > n:
        return 0
    return fac[n] * inv[k] % mod * inv[n - k] % mod
```

### 整除分块

```python
def divisor_blocks(n):
    """枚举所有 (l, r, n//l) 三元组，O(√n) 段。"""
    l = 1
    while l <= n:
        v = n // l
        r = n // v
        yield l, r, v
        l = r + 1
```

---

## B.14　动态规划

详见 [DP入门](../dp/basic.md) ~ [DP优化](../dp/opt/basic.md)。

```python
# 01 背包（整段取 max，比 Python 层循环快 5–8 倍）
f = [0] * (V + 1)
for v, w in items:
    if v > V:
        continue
    f[v:] = list(map(max, f[v:], [x + w for x in f[:V + 1 - v]]))

# 完全背包：二进制倍增（正序循环有串行依赖，无法直接 map）
kv, kw = v, w
while kv <= V:
    f[kv:] = list(map(max, f[kv:], [x + kw for x in f[:V + 1 - kv]]))
    kv += kv; kw += kw

# 多重背包：二进制拆分（先截断 s = min(s, V // v)，并特判 v == 0）
k = 1
while k <= s:
    add_01(k * v, k * w); s -= k; k += k
if s:
    add_01(s * v, s * w)

# 分组背包：组在外、物品在内，候选一律取自旧 f
for group in groups:
    tmp = f[:]
    for v, w in group:
        tmp[v:] = list(map(max, tmp[v:], [x + w for x in f[:V + 1 - v]]))
    f = tmp

# LIS O(n log n)：不下降用 bisect_right，严格上升用 bisect_left
tails = []
for x in a:
    p = bisect_right(tails, x)
    if p == len(tails):
        tails.append(x)
    else:
        tails[p] = x

# 树形 DP：BFS 序倒序 = 后序，连栈都不用（输入给出有向父子边时）
for u in reversed(bfs_order):
    merge_into_parent(u)
```

### 矩阵快速幂

```python
def mat_mul(A, B, mod):
    BT = list(zip(*B))                # 一次转置，避免内层按列取
    return [[sum(x * y for x, y in zip(row, col)) % mod for col in BT]
            for row in A]


def mat_pow(M, e, mod):
    n = len(M)
    R = [[int(i == j) for j in range(n)] for i in range(n)]
    while e:
        if e & 1:
            R = mat_mul(R, M, mod)
        M = mat_mul(M, M, mod)
        e >>= 1
    return R
```

> $n \le 10^7$ 时**直接线性递推更快**，别上矩阵。

---

## B.15　位运算

详见 [位运算](../basic/bit.md)。

```python
x & 1                    # 判奇偶
x >> 1                   # 除 2（向下取整）
x & (x - 1)              # 消去最低位的 1
x & (-x)                 # lowbit
x | (1 << k)             # 置 1
x & ~(1 << k)            # 清 0
x ^ (1 << k)             # 翻转
(x >> k) & 1             # 取第 k 位
bin(x).count("1")        # popcount（3.9）；3.10+ 用 x.bit_count()
x.bit_length()           # 二进制位数

# 枚举 mask 的所有子集，总量 O(3^n)
sub = mask
while True:
    ...
    if sub == 0:
        break
    sub = (sub - 1) & mask
```

> **写位运算一律加括号**——它的优先级低于比较运算符，`x & 3 == 1` 恒为 0。

---

## B.16　模板选型速查

碰到问题时先查这张表，避免用错工具。

| 需求 | 首选 | 备选 | 别用 |
| --- | --- | --- | --- |
| 排序 | `sorted` | — | 手写快排 |
| 判存在 | `set` | — | `x in list` |
| 队列 | `deque` / list+头指针 | — | `list.pop(0)` |
| 随机下标访问 | `list` | — | `deque[i]` |
| 区间和（静态） | `accumulate` 前缀和 | — | 每次重算 |
| 区间和（单点改） | 树状数组 | 分块 | 递归线段树 |
| 区间改 + 区间查 | 双树状数组差分 | 非递归线段树 | 递归线段树 |
| 区间最值（静态） | ST 表 | 分块 | 线段树 |
| 前驱 / 后继 | 值域位图 | 树状数组 + 倍增 | `sortedcontainers`（没装） |
| 无权图最短路 | BFS | — | Dijkstra |
| 0/1 权最短路 | 0-1 BFS | — | Dijkstra |
| 非负权最短路 | 堆优化 Dijkstra | — | SPFA |
| 字符串匹配 | `str.find` | KMP | 手写朴素 |
| 求周期 / border | KMP 前缀函数 | 哈希 | — |
| 全排列 | `itertools.permutations` | — | 手写回溯 |
| 幂取模 | `pow(a,b,m)` | — | 手写快速幂 |
| 整数开方 | `math.isqrt` | — | `x ** 0.5` |
| 严格四舍五入 | `Decimal` + `ROUND_HALF_UP` | — | `round` / `%.nf` |
| 图上 DFS | 迭代（显式栈） | 大栈线程 | 直接递归 |
| 树形 DP | BFS 序倒序 | 迭代后序 | 直接递归 |
| DP 内层循环 | `map` / 切片批处理 | — | Python 层 for |

> 完整的避坑清单见 [附录 C](c-pitfalls.md)。

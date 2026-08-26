---
id: dp/dag
title: DAG 上的 DP
volume: 2
lang: py
---

# 第 103C 章　DAG 上的 DP

<!-- CHAPTER-EXAMPLES -->
> **前置**：[拓扑排序](../graph/topo.md)、[DP 入门](basic.md)

DAG 上的动态规划与树形动态规划同源，但拓扑序取代了后序。

$$f[u] = \text{merge}\big(f[v] \mid u \to v\big)$$

**必须按拓扑序处理**（或反拓扑序，取决于转移方向）。

**拓扑序就是无后效性的来源**：处理 $u$ 时它的所有前驱都已算完。
[拓扑排序](../graph/topo.md) 讲的是「为什么能这么算」，本章讲「能算什么」。

> 拓扑排序模板见 [拓扑排序](../graph/topo.md)。

同源的另外三种形态：[区间 DP](interval.md)、[树形 DP](tree.md)、[状压 DP](state.md)。

> **计数版本**：把 $\min$/$\max$ 换成 $+$ 就是计数 DP，取模的时机与陷阱见 [DP 入门 · 计数 DP 与取模](basic.md#8-计数-dp-与取模)。

---

## 1　模板与可线性求解的模型

按拓扑序遍历，处理 $u$ 时它的所有前驱都已算完，直接往后继推：

```python
def dag_longest_path(n, start, adj, order):
    """DAG 上以每个点为终点的最长路（按点数计）。O(n + m)。

    对应经典题「旅行计划」：f[v] = 1 + max(f[u])，u 是 v 的前驱。
    order 由 topo_sort 给出。若要按边权计，把 1 换成 wt[i]。
    """
    f = [1] * (n + 1)                        # 每个点自己算 1 个
    for u in order:                          # ★ 按拓扑序推，前驱一定已经定好
        fu = f[u] + 1                        # 从 u 再走一条边到后继，长度 +1
        for i in range(start[u], start[u + 1]):
            v = adj[i]
            if fu > f[v]:
                f[v] = fu                    # 「往后推」而不是「回头找前驱」，省一次反图
    return f                                 # 处理到 u 时 f[u] 已终值，不会再被改


def dag_count_paths(n, start, adj, order, src, mod=1000000007):
    """从 src 出发到每个点的路径条数。O(n + m)。"""
    cnt = [0] * (n + 1)
    cnt[src] = 1                             # 起点自己算一条「空路径」
    for u in order:                          # 拓扑序保证 cnt[u] 在被读走时已经是终值
        c = cnt[u]
        if c:                                # 不可达的点不用往下推
            for i in range(start[u], start[u + 1]):
                cnt[adj[i]] = (cnt[adj[i]] + c) % mod   # 每次累加就取模，数值不膨胀
    return cnt
```

| DAG 上能线性做的问题 | 说明 |
| --- | --- |
| 最长路 / 最短路 | **边权可以是负数**，不需要 Dijkstra 也不需要 Bellman-Ford |
| 路径计数 | 上面的 `dag_count_paths` |
| 每个点能到达多少个点 | 逆拓扑序 + `bitset`（Python 用大整数当位集，见 [位运算](../basic/bit.md)） |
| 最小路径覆盖 | $n - $ 二分图最大匹配（见 [二分图](../graph/match/bipartite.md)） |
| 关键路径（AOE 网） | 正推 `ve`、逆推 `vl`，`ve == vl` 的活动即关键活动 |

> **DAG 最短路允许负权，这是它和一般图最重要的区别**。
> Dijkstra 要求非负权，Bellman-Ford 要 $O(nm)$；
> 而 DAG 上按拓扑序一遍递推就是 $O(n+m)$，负权照做。
> 「无环」这个条件的价值就在这里。见 [最短路](../graph/shortest-path.md)。

**关键路径**（AOE 网、工程最早/最晚完工时间）是 DAG 最长路的直接应用，
完整讲解在 [图论进阶：k短路与关键路径](../graph/kth-path.md)。

---

## 2　例题

<!-- CHAPTER-EXAMPLE-TABLE -->

### BISHI144 食物链计数（较难）

> 求 DAG 上从「入度为 0 的点」到「出度为 0 的点」的路径条数。$n, m \le 10^5$。

$$
f[x] = \begin{cases}
1 & x \text{ 出度为 } 0 \\
\sum_{x \to y} f[y] & \text{否则}
\end{cases}
$$

答案 $= \sum_{\text{入度为 0 的 } x} f[x]$。

实现上按「**出度**」做 Kahn：先把出度为 0 的点入队；出队 $v$ 时把 $f[v]$ 累加给所有前驱 $u$，
并把 $u$ 的出度减 1，减到 0 就入队。这样天然是**逆拓扑序**，不需要显式排序。

> **坑 1（最容易错）**：**方向别搞反**。输入 `u v` 表示「$v$ 捕食 $u$」，即有向边 $u \to v$；
> 而 $f$ 是沿边**正向**走到出度 0 的点的方案数，所以递推要用**反向邻接表**。
>
> **坑 2**：题面文字与样例说明略有出入（说明里把 8 也列成了生产者）。
> **以形式化定义为准**：出度为 0 = 链的一端，入度为 0 = 链的另一端。
> 按样例验算 $f(1) = 2+3+4 = 9$，与期望输出一致，确认定义无误。
>
> **坑 3**：孤立点（入度出度都是 0）自成一条链，计入答案 1——公式天然覆盖，不用特判。

题解：[`solutions/nowcoder/BISHI144/sol.py`](../solutions/BISHI144.md)（已通过官方样例验证）

---

## 3　本章速查

| 形态 | 状态载体 | 枚举顺序 | 「最后一步」是什么 |
| --- | --- | --- | --- |
| DAG DP | 点 | **拓扑序 / 逆拓扑序** | 走哪条出边 |

| Python 关键 | 做法 |
| --- | --- |
| DAG DP | 本章唯一 Python 无劣势的形态 |

| DAG 上能线性做的问题 | 见上一节的对照表 |
| --- | --- |
| 最长路 / 最短路 | **边权可以是负数** |
| 路径计数 | `dag_count_paths`，每步取模 |
| 关键路径（AOE 网） | 正推 `ve`、逆推 `vl` |

---
id: search/iterative-deepening
title: 迭代加深与 IDA*
volume: 3
lang: py
---

# 第 115A 章　迭代加深与 IDA\*

> **状态：待扩写。** 本章目前只有 IDA\* 一节。
> 与 [DFS](dfs.md)、[记忆化搜索与剪枝](memoization.md) 的分工、
> 更多估价函数设计与例题尚未写入。

> **前置**：[DFS深度优先搜索](dfs.md)、[记忆化搜索与剪枝](memoization.md)

迭代加深（IDDFS）是「限深 DFS，深度从 1 逐次加 1」：答案深度小、分支因子大、
BFS 会 MLE 时用它。**IDA\*** 在此之上装一个乐观估价函数 $h$，
用「已走步数 $+\ h >$ limit 就返回」把搜索树再砍一刀。

IDDFS 本身讲在 [记忆化搜索与剪枝](memoization.md)，本章只讲装上 $h$ 之后的部分。

---

## 1　IDA\*：给 IDDFS 装上估价函数

IDDFS 的限深循环里加一条剪枝：

$$\text{已走步数} + h(\text{当前状态}) > \text{limit} \;\Longrightarrow\; \text{直接返回}$$

$h$ 必须是**乐观估计**（$h \le$ 真实剩余步数），即所谓 **admissible**；
否则会剪掉最优解，答案偏大。

```python
# [片段]
def ida_star(start, is_goal, neighbors, h, max_limit=100):
    """IDA*：迭代加深 + 乐观估价函数。返回最少步数，找不到返回 -1。

    h(u) 必须满足 h(u) <= 真实剩余步数（乐观），否则结果可能非最优。
    空间 O(d)，这是它相对 A* 的唯一优势（A* 要存整个优先队列）。
    """

    def dfs(u, g, limit):
        f = g + h(u)                         # g 是已走步数，h 是剩余步数的乐观下界
        if f > limit:
            return f                         # ★ 返回「超出的最小 f」，用于下一轮的 limit
        if is_goal(u):
            return -1                        # 用 -1 表示找到
        nxt = limit + 1                       # 下一轮 limit 的候选：所有被剪掉的 f 的最小值
                                              # 初值比 limit 大 1，保证任何真实的 f 都能压过它
        for v in neighbors(u):
            r = dfs(v, g + 1, limit)
            if r == -1:
                return -1                     # 子树里找到了，一路向上直接返回
            if r < nxt:
                nxt = r                       # 收集被剪掉的最小 f
        return nxt

    limit = h(start)                          # 起始上限取估价值：比它小的深度不可能有解
    while limit <= max_limit:
        r = dfs(start, 0, limit)
        if r == -1:
            return limit                      # h 乐观 -> 第一次找到时的 limit 就是最优步数
        limit = r                            # ★ 下一轮直接跳到最小的越界 f，不是 limit+1
    return -1
```

> **`limit = r` 而不是 `limit += 1` 是 IDA\* 的精髓**：
> 下一轮的深度上限直接取「本轮所有被剪掉的 $f$ 值的最小值」，
> 一次跳到位，避免了大量无效的中间轮次。边权全为 1 时两者等价，
> 边权不等时前者能快好几倍。

**常见估价函数**：

| 问题 | $h$ |
| --- | --- |
| 八数码 / 十五数码 | 各数字到目标位置的**曼哈顿距离之和** |
| 魔方 | 各面错位块数 / 8（每次转动最多修好 8 块） |
| **重复覆盖**（最少行数盖住所有列） | 贪心地「选一列 → 删掉能盖它的所有行覆盖的列」的轮数 |
| 木棒拼接 | 剩余木棒总长 / 目标长度 |

---

## 2　本章速查

| 要点 | 结论 |
| --- | --- |
| **IDA\*** | IDDFS + 乐观估价 $h$；`limit` 取「被剪掉的最小 $f$」 |
| $h$ 必须乐观 | $h \le$ 真实剩余步数（admissible），否则答案偏大 |
| 典型搭档 | **重复覆盖**（最少行数盖住所有列），见 [精确覆盖与 Dancing Links](dlx.md) |

| 数据规模 → Python 现实性 |
| --- |
| 重复覆盖 + IDA\*，规模稍大 | ❌ 常数再叠一层，基本没戏 |

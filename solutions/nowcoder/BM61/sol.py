# 来源: 牛客 · 面试必刷TOP101　中等
# 链接: https://www.nowcoder.com/practice/7a71a88cdf294ce6bdf54c899be967a2
# 判题: 核心代码模式
# 签名: solve(matrix: integer[][]) -> integer

"""BM61 矩阵最长递增路径 —— 按数值从大到小推 dp，dp[i][j] = 1 + 更大邻居里的最大 dp。

这题考什么：
    设 dp[i][j] 为「从 (i,j) 出发」能走出的最长递增路径长度，答案就是所有 dp 的最大值。
    转移显然：

        dp[i][j] = 1 + max(dp[邻居])   仅取值严格大于 matrix[i][j] 的邻居
        没有更大的邻居时 dp[i][j] = 1

    因为路径必须**严格递增**，从 (i,j) 走出去之后不可能再绕回来（值只增不减），
    所以这张图天然无环，dp 有良定义，也不必再记 visited。

    朴素写法是记忆化搜索，但矩阵可到 1000*1000，
    一条蛇形递增的路径能让递归深到 1e6 层，Python 直接爆栈。
    这里改成**按拓扑序迭代**，而这题的拓扑序不用另算——就是数值从大到小：
    处理到值为 v 的格子时，它所有「值 > v」的邻居都已经算完了；
    同一桶内的格子值相等、彼此之间没有边，先后顺序随意。

        1 2 3      按值降序处理 9,8,7,6,5,4,3,2,1
        4 5 6      dp[9]=1, dp[6]=2, dp[3]=3, dp[2]=4, dp[1]=5  ->  1->2->3->6->9
        7 8 9

    DAG 上按拓扑序递推的一般写法见 docs/graph/topo.md。

数据规模与复杂度：
    1 <= n,m <= 1000（最多 1e6 个格子），0 <= matrix[i][j] <= 1000（值域 1001 档），
    时限「C/C++ 3 秒，其他语言 6 秒」——比这套题单常见的 2 秒宽，正是因为规模大。
    分桶 O(nm + V)、主循环每格看四个邻居 O(4nm)，合计 O(nm + V)，对上题面进阶要求；
    空间 O(nm)（dp 表加桶）。
    改用排序求拓扑序是 O(nm log nm)，1e6 * 20 = 2e7 次比较，Python 上明显更慢；
    值域只有 1001 档时桶排是白捡的便宜。

坑在哪：
  1. 记忆化搜索在这题上不是等价选项：1000*1000 的蛇形递增矩阵能让递归深度到 1e6，
     远超 Python 默认的 1000 层上限，而调高 setrecursionlimit 又会撞爆 C 栈。
     迭代按拓扑序推 dp 才稳。
  2. 拓扑序为什么就是数值降序：dp[i][j] 只依赖**值严格大于**它的邻居，
     所以轮到值 v 时，一切可能被引用的格子都在更早的桶里定稿了，一遍扫过去无需回头。
  3. 邻居判定必须是严格大于。写成 >= 会在相等的相邻格之间造出双向边，
     图不再无环，dp 的定义随之失效（互相引用，谁也算不出来）。
  4. dp 初值取 1 而不是 0：单个格子本身就是一条长度为 1 的路径，
     题面示例 2 的 [[1,2],[4,3]] 答案是 3，全 0 起步会整体差 1。
  5. 桶下标要减去最小值做偏移（buckets[v - lo]）：矩阵值域虽从 0 起，
     但按实际出现的最小值开桶更省内存，代价是取用时必须记得同一套偏移。
  6. 答案初值取 1 而非 0：题面保证 n,m >= 1，矩阵非空时最短路径也有 1 格。

样例复核：
    [[1,2,3],[4,5,6],[7,8,9]]：9 的四邻没有更大的，dp=1；6 的邻居 9 更大，dp=2；
    3 的邻居 6 更大，dp=3；2 -> 3 得 dp=4；1 -> 2 得 dp=5。最大值 5，与示例 1 一致。
"""
from typing import List, Optional


class Solution:
    def solve(self, matrix: List[List[int]]) -> int:
        if not matrix or not matrix[0]:
            return 0
        n, m = len(matrix), len(matrix[0])

        lo = min(min(row) for row in matrix)
        hi = max(max(row) for row in matrix)
        # 桶排：buckets[v - lo] 收集所有取值为 v 的坐标，取代 O(nm log nm) 的排序
        buckets: List[List[tuple]] = [[] for _ in range(hi - lo + 1)]
        for i in range(n):
            row = matrix[i]
            for j in range(m):
                buckets[row[j] - lo].append((i, j))

        # dp[i][j] = 从 (i,j) 出发的最长递增路径长度；单个格子自成一条路径，故初值 1
        dp = [[1] * m for _ in range(n)]
        ans = 1
        # 从大到小就是这张 DAG 的拓扑序：轮到 v 时，所有比它大的邻居都已定稿
        for b in range(hi - lo, -1, -1):
            for i, j in buckets[b]:
                v = matrix[i][j]
                best = 1
                # 只取值严格大于自己的邻居：相等不构成递增边，写成 >= 会造出环
                for x, y in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)):
                    if 0 <= x < n and 0 <= y < m and matrix[x][y] > v:
                        cand = dp[x][y] + 1
                        if cand > best:
                            best = cand
                dp[i][j] = best
                # 答案是所有起点的最大值，顺手在推 dp 的同时统计，省一遍扫描
                if best > ans:
                    ans = best
        return ans

"""BISHI104 修复公路 —— 每条路有修完时刻，问最早何时全国连通。

这题考什么：
    「最早连通时刻」= 把边按修完时间升序一条条加入，
    **让全图连通的那条边的时间**。这正是 Kruskal 的过程（最小生成树的
    最大边 = 瓶颈生成树的瓶颈值），所以：
        排序 + 并查集，加到第 N-1 次成功合并时，当前边的 t 就是答案。
    Kruskal 与最小生成树见 docs/graph/mst.md，
    并查集见 docs/ds/dsu.md。
    加完全部边仍未连通 -> 输出 -1。

数据规模与复杂度：
    N <= 1e3，M <= 1e5。排序 O(M log M) ≈ 1.7e6，并查集近似 O(M α)。
    （也可以二分时间 + 每次并查集验证，但那是 O(M log M α)，
      没有必要——Kruskal 一遍扫过去就够。）

Python 的坑：
  1. 并查集的 find 写**迭代**路径压缩 + 按大小合并，不用递归；
  2. 排序时只按 t 排即可，用 `edges.sort(key=...)` 不如直接把 t 放在元组第一位
     再 sort()——省掉一次 Python 函数调用，1e5 条边差别明显；
  3. 输入 3e5 个整数，一次 read().split() 读完。

坑在哪：
  1. **N = 1 时不需要任何边**，答案是 0（一个城市自己和自己天然通车）。
     不特判的话循环会一条边都不满足「第 N-1 次合并」而错误输出 -1；
  2. 可能有重边、自环，Kruskal 自动忽略（同根就跳过），不必预处理；
  3. 计数用「成功合并的次数」，不是「扫过的边数」。

样例复核：
    边按 t 排序：(3,4-2) (4,1-3) (5,1-4) (6,1-2)。
    合并 4-2 ✓、1-3 ✓、1-4 ✓ 此时 {1,2,3,4} 连通，第 3 = N-1 次合并，答案 5 ✓
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n, m = int(data[0]), int(data[1])
    if n == 1:                                 # 只有一个城市，无需修路
        sys.stdout.write("0\n")
        return

    # ---- 读边并按修完时间升序排序，这就是 Kruskal 的第一步 ----
    edges = [None] * m
    p = 2
    for i in range(m):
        x = int(data[p]); y = int(data[p + 1]); t = int(data[p + 2]); p += 3
        edges[i] = (t, x, y)                   # t 放首位，直接 sort 即按时间升序
    edges.sort()                               # 元组先比较首项，等价于按时间升序

    parent = list(range(n + 1))                # 并查集：初始每座城市各成一个连通块
    size = [1] * (n + 1)                       # size 只在根上有意义

    def find(x: int) -> int:
        """迭代式路径压缩，避开退化成长链时的递归深度问题。"""
        r = x
        while parent[r] != r:                  # 第一趟：向上找到根
            r = parent[r]
        while parent[x] != r:                  # 第二趟：把沿途节点直接挂到根上
            parent[x], x = r, parent[x]
        return r

    # ---- 按时间从早到晚加边，第 n-1 次成功合并时全国刚好连通 ----
    need = n - 1                               # 还差多少次「有效合并」
    for t, x, y in edges:
        rx, ry = find(x), find(y)
        if rx == ry:
            continue                           # 两端早已连通（重边 / 自环），不计数
        if size[rx] < size[ry]:                # 按大小合并：小树挂到大树下
            rx, ry = ry, rx
        parent[ry] = rx
        size[rx] += size[ry]
        need -= 1
        if need == 0:                          # 第 n-1 次成功合并 -> 全图连通
            sys.stdout.write("%d\n" % t)       # 这条边的修完时间即最早连通时刻
            return
    sys.stdout.write("-1\n")                   # 全部修完仍有城市互不可达


main()

"""BISHI107 【模板】最小生成树 I ‖ 稀疏图：Kruskal —— 求 MST 边权和，不连通输出 NO。

这题考什么：
    Kruskal：边按权值升序排序，依次尝试加入，用并查集判「这条边的两端是否
    已经连通」，不连通就加进生成树。加满 n-1 条即得 MST（最小生成树）；
    扫完所有边仍不足 n-1 条说明图不连通。

    并查集（DSU，disjoint set union，中文也叫「不相交集合」）：
    每个连通块用一棵树表示，树根是这个块的代表元。find(x) 顺着 parent 一路
    走到根即可判断「x 和 y 是不是同一块」，union 把一棵树的根挂到另一棵下面。
    配上路径压缩与按大小合并后，单次操作几乎是常数时间。
    见 docs/ds/dsu.md 与 docs/graph/mst.md。

数据规模与复杂度：
    n, m <= 3e5。排序 O(m log m) ≈ 3e5 * 18，并查集近似线性。
    稀疏图（m 与 n 同阶）用 Kruskal 最合适；稠密图才轮到 Prim + 堆。

Python 的坑：
  1. 并查集的 find 必须写**迭代**路径压缩（3e5 规模的退化链会让递归爆栈），
     再配上按大小合并；
  2. 排序时把权值放在元组第一位后直接 `edges.sort()`，
     比 `sort(key=lambda e: e[2])` 少 3e5 次 Python 函数调用，快得多；
  3. 3e5 条边、9e5 个整数，一次 read().split() 读完再切片转换。

坑在哪：
  1. **边权可以是负数**（-1e9 <= w <= 1e9）。这不影响 Kruskal 的正确性
     （MST 的贪心证明不依赖权值非负），但答案可能是负数，
     所以不能用「答案初始化为 0 且只加正数」之类的偷懒写法；
     样例 2 里就有 -12 这样的边；
  2. n = 1 时不需要任何边，MST 权和是 0，且图算连通 —— 循环里 need = 0
     一开始就满足，要保证这种情况输出 0 而不是 NO；
  3. 有重边、无自环，Kruskal 天然处理（同根跳过）。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n, m = int(data[0]), int(data[1])

    # ---- 读边并按权升序排序，这是 Kruskal 贪心的前提 ----
    edges = [None] * m
    p = 2
    for i in range(m):
        u = int(data[p]); v = int(data[p + 1]); w = int(data[p + 2]); p += 3
        edges[i] = (w, u, v)                  # 权值放首位，sort() 即按权升序
    edges.sort()

    # ---- 并查集：一开始每个点自成一块 ----
    parent = list(range(n + 1))               # parent[x] == x 表示 x 是代表元
    size = [1] * (n + 1)                      # 每块的点数，用于按大小合并

    def find(x: int) -> int:
        r = x
        while parent[r] != r:                 # 先一路走到代表元
            r = parent[r]
        while parent[x] != r:                 # 迭代路径压缩
            parent[x], x = r, parent[x]       # 把沿途每个点直接挂到根上，下次就是一步
        return r

    # ---- 贪心扫边：能连就连，直到凑够 n-1 条 ----
    need = n - 1                              # n = 1 时开局就是 0
    total = 0
    for w, u, v in edges:
        if need == 0:
            break                             # 已经是一棵树了，剩下的边只会成环
        ru, rv = find(u), find(v)
        if ru == rv:
            continue                          # 两端同块，加进来必成环（重边也在这里被滤掉）
        if size[ru] < size[rv]:               # 按大小合并：小块挂到大块下，树高才不会退化
            ru, rv = rv, ru
        parent[rv] = ru
        size[ru] += size[rv]
        total += w                            # w 可能为负，照加不误
        need -= 1
    # need > 0 说明扫完全部边仍连不成一棵树，图不连通
    sys.stdout.write(("%d\n" % total) if need == 0 else "NO\n")


main()

"""BISHI81 剪纸游戏 —— 数「被剪掉的 '.' 四连通块」里有多少个恰好是实心长方形。

这题考什么：
    连通块搜索 + 一个很干净的判定小技巧：
        一个连通块是实心长方形  <=>  它的格子数 == 其外接矩形的面积。
    因为外接矩形的面积一定 >= 块的大小，取等号说明外接矩形被填满、没有缺口，
    同时也自动排除了「L 形 / 空心 / 十字形」这些情况。
    所以只要在 BFS 过程中顺手维护 minr / maxr / minc / maxc 和计数即可，
    不需要真的去逐格验证矩形内部。

数据规模与复杂度：
    n, m <= 1000 -> 1e6 个格子。每格入队出队各一次，O(nm)。

Python 的坑：
  1. 队列用 collections.deque；1e6 个点用 list.pop(0) 会直接退化成平方级；
  2. 网格压成一维 + 四周加 '*' 哨兵边框，省掉 4 次边界判断；
     还原行列时用 divmod(idx, W)；
  3. 「入队时立刻标记已访问」（这里直接把 grid 上的 '.' 改写成 '*'），
     否则同一格会被 4 个邻居重复入队，队列规模会爆；
  4. grid 用 bytearray 而不是 list of str，比较的是 int，快且省内存。

题面歧义：
    题面说被剪下的图案「互不连通」，因此每个 '.' 连通块 = 一个图案，
    这里按四连通理解（斜着挨着的两块沿网格线是可以分开剪的）。
    样例 4x10 的那组数据按四连通算恰好得到 4，验证了这个理解。
"""
import sys
from collections import deque


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n, m = int(data[0]), int(data[1])
    rows = data[2:2 + n]

    W = m + 2
    CUT = ord('.')
    grid = bytearray(b'*' * W)
    for r in rows:
        grid += b'*' + r + b'*'
    grid += b'*' * W

    ans = 0
    q = deque()
    # 扫描范围掐掉首尾两行哨兵；左右两列哨兵是 '*'，会被下面的判断直接跳过
    for start in range(W, len(grid) - W):
        if grid[start] != CUT:
            continue
        grid[start] = ord('*')            # 入队即标记
        q.append(start)
        r0, c0 = divmod(start, W)         # 一维下标还原成 (行, 列)
        minr = maxr = r0                  # 外接矩形初值取起点自身
        minc = maxc = c0
        size = 0
        while q:
            u = q.popleft()
            size += 1
            r, c = divmod(u, W)
            # 一个坐标不可能同时小于最小值又大于最大值，用 elif 少做一次比较
            if r < minr: minr = r
            elif r > maxr: maxr = r
            if c < minc: minc = c
            elif c > maxc: maxc = c
            for v in (u - W, u + W, u - 1, u + 1):
                if grid[v] == CUT:
                    grid[v] = ord('*')    # 改写原图当访问标记，入队即改，省一个 vis
                    q.append(v)
        # 块大小 == 外接矩形面积 <=> 实心长方形
        if size == (maxr - minr + 1) * (maxc - minc + 1):
            ans += 1
    sys.stdout.write("%d\n" % ans)


main()

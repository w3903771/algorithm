"""BISHI77 数水坑 —— N*M 网格里数「八连通」的 'W' 连通块个数。

这题考什么：
    连通块计数模板。唯一和常规题不同的是**八连通**（含四条对角线），
    方向数组要写 8 个偏移量，写成 4 个就会把斜着搭在一起的水格拆成两块。

数据规模与复杂度：
    N, M <= 100，格子 1e4 个。每个 'W' 只会被访问一次（入栈时立刻标记），
    每次访问看 8 个邻居，总复杂度 O(8NM)，毫秒级。

Python 的坑（本题必看）：
    最坏情况整张图全是 'W'，一个连通块就有 1e4 个格子，递归 DFS 的深度
    直接 1e4 层，超过默认 1000 的递归上限必 RecursionError。
    **所以写成显式栈的迭代 DFS**，栈深度由 list 承载，和解释器上限无关。

其它坑：
  1. 「入栈时就标记 visited」而不是「出栈时才标记」，否则同一个格子会被
     多个邻居重复压栈，栈会膨胀到 O(8NM) 甚至更糟；
  2. 直接把已访问的格子在原图上改写成 '.' 也可以省一个 vis 数组，但输入是
     不可变的 bytes，这里用 bytearray 的 vis 更直观。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n, m = int(data[0]), int(data[1])
    g = data[2:2 + n]
    W = ord('W')

    vis = [bytearray(m) for _ in range(n)]
    cnt = 0
    for si in range(n):
        row = g[si]
        vrow = vis[si]
        for sj in range(m):
            if row[sj] != W or vrow[sj]:
                continue
            cnt += 1
            vrow[sj] = 1
            stack = [(si, sj)]
            while stack:
                x, y = stack.pop()
                # 八连通：上下左右 + 四个斜角
                for dx in (-1, 0, 1):
                    nx = x + dx
                    if nx < 0 or nx >= n:
                        continue
                    gr, vr = g[nx], vis[nx]
                    for dy in (-1, 0, 1):
                        ny = y + dy
                        if 0 <= ny < m and not vr[ny] and gr[ny] == W:
                            vr[ny] = 1          # 入栈即标记，防止重复入栈
                            stack.append((nx, ny))
    sys.stdout.write("%d\n" % cnt)


main()

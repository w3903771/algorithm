"""BISHI82 没挡住洪水 —— N*N 网格，问有多少个 '#' 四连通区域会在一天后被「完全」淹没。

这题考什么：
    连通块搜索 + 读题。洪水上涨的规则是：
        「所有与 '.' 上下左右相邻的 '#' 都会被淹」。
    注意这是**一次性、同时**发生的一轮，不是反复扩散到收敛。
    所以一个区域被「完全」淹没 <=> 区域里的**每一个**格子都至少有一个
    四方向邻居是 '.'。于是只要在遍历连通块时对每个格子检查一遍邻居即可。

    常见错解：以为洪水会一轮轮往里渗，于是判定成「区域全被淹」总是成立；
    或者只判「区域边界挨着水」就算完全淹没——那只淹掉了外壳，
    厚度 >= 3 的实心块中心是淹不到的。

数据规模与复杂度：
    N <= 1000 -> 1e6 格。每格入队一次、看 4 个邻居，O(N^2)。

Python 的坑：
  1. 队列用 collections.deque，1e6 规模下 list.pop(0) 必然退化；
  2. 网格压一维 + 四周补 '.' 哨兵。题面已保证四条边界全是被淹区域，
     补 '.' 与题意一致，同时消除了越界判断；
  3. 入队即标记（把 '#' 改写成已访问标记 'x'），避免重复入队；
  4. 判定「该格是否会被淹」时要用**原始**地图的 '.'，
     所以已访问标记不能也写成 '.'，否则会把同区域的兄弟格误判成水。
     这里用第三种字符 'x' 区分。

其它坑：
  1. 洪水只涨**一轮**。写成「反复扩散直到不再变化」的话，任何区域最终都会被
     淹完，答案会变成区域总数；
  2. 「完全淹没」要求区域里每一格都挨着水，因此 all_flooded 必须在整块搜完之后
     才下结论：中途遇到一个不挨水的格子就置 False，但不能提前退出，
     否则这块区域剩下的格子不会被标记，会被当成新区域重复计数；
  3. 补的一圈哨兵是 '.'，与题面「边界四条边全部已被淹没」一致，所以贴边的
     陆地会被哨兵正确判成「挨着水」，不是为了省判断而人为放水；
  4. 一格都没有陆地时答案是 0（样例的 N=1 全是 '.' 就是这种情况）。
"""
import sys
from collections import deque


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    rows = data[1:1 + n]

    W = n + 2
    LAND = ord('#')
    WATER = ord('.')
    SEEN = ord('x')                       # 第三种字符：已访问的陆地
    grid = bytearray(b'.' * W)
    for r in rows:
        grid += b'.' + r + b'.'
    grid += b'.' * W

    ans = 0
    q = deque()
    # 扫描范围掐掉首尾哨兵行；左右两列哨兵是 '.'，不会被当成陆地
    for start in range(W, len(grid) - W):
        if grid[start] != LAND:
            continue                      # 水、或已归入某个区域的陆地
        grid[start] = SEEN
        q.append(start)
        all_flooded = True                # 先假定整块都会被淹，遇到反例再推翻
        while q:
            u = q.popleft()
            touched = False               # 本格是否挨着水
            for v in (u - W, u + W, u - 1, u + 1):
                c = grid[v]
                if c == WATER:
                    touched = True        # 只有原始的 '.' 算水，SEEN 不算
                elif c == LAND:
                    grid[v] = SEEN        # 入队即标记，避免重复入队
                    q.append(v)
            if not touched:
                all_flooded = False       # 有一格淹不到，整块就不算完全消失
                                          # 但不能在这里 break：整块必须搜完并标记
        if all_flooded:
            ans += 1
    sys.stdout.write("%d\n" % ans)


main()

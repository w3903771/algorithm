"""BISHI83 迷宫问题 —— h*w 的 01 迷宫，输出一条从 (0,0) 到 (h-1,w-1) 的可行路径。

这题考什么：
    BFS 求最短路 + **前驱数组回溯路径**。题目保证可行路径唯一，
    所以「最短路」和「那条唯一路径」是同一条；用 BFS 既能保证找到，
    又能顺手用 pre[] 把路径倒着串回来。

数据规模与复杂度：
    h, w <= 100 -> 至多 1e4 个格子，O(hw)。

Python 的坑（本题必看）：
  1. **队列必须用 collections.deque**，list.pop(0) 是 O(n)；
  2. 这题常见写法是递归 DFS + 回溯，但最坏路径长度是 hw = 1e4，
     递归深度会直接撞破 CPython 默认 1000 层的上限。
     **本解改用 BFS（天然迭代）+ pre 数组**，完全不碰递归；
     即便要用 DFS 也应该写显式栈，而不是 sys.setrecursionlimit 硬顶；
  3. 回溯出来的路径是「终点 -> 起点」，最后要 reverse；
  4. 输入是 h*w 个**空格分隔的 0/1 整数**（不是一整行字符串），
     用 split() 按 token 读正好。

输出格式坑：
    「输出描述」写的是「输出两个整数 x_i, y_i」，但样例输出的实际格式是
    带括号无空格的 "(x,y)"。以样例为准，输出 "(x,y)"。
"""
import sys
from collections import deque


def main() -> None:
    data = sys.stdin.buffer.read().split()
    h, w = int(data[0]), int(data[1])
    g = data[2:2 + h * w]                 # b'0' / b'1'

    WALL = b'1'
    n = h * w
    # pre 一物三用：-2 未访问（兼作 visited 标记）、-1 起点（回溯的终止哨兵）、
    # 其余存前驱的一维下标。省掉单独的 vis 数组，本题空间限制只有 64MB
    pre = [-2] * n                        # -2 未访问，-1 起点，其余为前驱下标
    start, goal = 0, n - 1                # (0,0) 与 (h-1,w-1) 压成一维后的下标
    pre[start] = -1
    q = deque([start])
    while q:
        u = q.popleft()
        if u == goal:
            break                         # 到终点即可停，pre 链已经完整
        x, y = divmod(u, w)               # 一维下标还原成 (行, 列)，用来做边界判断
        # 四个方向分开写：先用行列判断不越界，再按 ±1 / ±w 算邻居下标。
        # 这样能避免「最左格 -1 跑到上一行末尾」这类横向绕回的错误
        if x > 0:
            v = u - w
            if pre[v] == -2 and g[v] != WALL:
                pre[v] = u; q.append(v)
        if x + 1 < h:
            v = u + w
            if pre[v] == -2 and g[v] != WALL:
                pre[v] = u; q.append(v)
        if y > 0:
            v = u - 1
            if pre[v] == -2 and g[v] != WALL:
                pre[v] = u; q.append(v)
        if y + 1 < w:
            v = u + 1
            if pre[v] == -2 and g[v] != WALL:
                pre[v] = u; q.append(v)

    # 回溯：从终点沿 pre 一路跳回起点，pre[start] = -1 是循环的出口
    path = []
    u = goal
    while u != -1:                        # 从终点顺着 pre 倒推回起点
        x, y = divmod(u, w)
        path.append("(%d,%d)" % (x, y))
        u = pre[u]
    path.reverse()                        # 倒推出来是「终点 -> 起点」，翻转成正序
    sys.stdout.write("\n".join(path) + "\n")


main()

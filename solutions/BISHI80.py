"""BISHI80 走迷宫 —— n*m 网格四联通，求起点到终点的最少步数，不可达输出 -1。

这题考什么：
    无权图单源最短路 = BFS。每条边权都是 1，BFS 出队顺序天然按层，
    第一次访问到某格时的步数就是最短步数。

数据规模与复杂度：
    n, m <= 1000 -> 最多 1e6 个格子、4e6 条有向边。O(nm) 是唯一可行做法
    （Dijkstra 会白白多一个 log，DFS 求最短路则是错的）。

Python 的坑（本题必看）：
  1. **队列必须用 collections.deque**。用 list + pop(0) 的话，每次弹头都要
     搬移整个列表，1e6 个点会退化成 O(n^2) ≈ 1e12，必然 TLE；
  2. 把二维网格**压成一维数组**（idx = i * W + j），并在四周加一圈墙做哨兵，
     这样内层循环里不需要写 4 次边界判断，只做一次 grid 查表，常数能省一半；
  3. dist 用 bytearray 存不下（步数可达 1e6），用 list of int；用 -1 表示未访问，
     既是「未访问」标记又是最终输出的「不可达」值，一举两得；
  4. 输入坐标是 1-based，加了哨兵边框后正好可以直接用，不用 -1 再 +1。

其它坑：
    起点保证可通行，但**终点不保证**（样例 2/3 就是走不到）。
    起点 == 终点时答案是 0，要能正确落到 dist[start] = 0 上。
"""
import sys
from collections import deque


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n, m = int(data[0]), int(data[1])
    xs, ys, xt, yt = int(data[2]), int(data[3]), int(data[4]), int(data[5])
    rows = data[6:6 + n]

    W = m + 2                            # 每行左右各补一格哨兵，所以宽度是 m+2
    BLOCK = ord('*')
    # 压成一维并加一圈 '*' 哨兵，越界判断就被墙自动挡掉了
    grid = bytearray(b'*' * W)           # 顶部哨兵行
    for r in rows:
        grid += b'*' + r + b'*'
    grid += b'*' * W                     # 底部哨兵行

    # 有了哨兵边框，1-based 的输入坐标正好就是一维下标：第 1 行落在第 1 行
    s = xs * W + ys
    t = xt * W + yt
    dist = [-1] * len(grid)              # -1 兼作「未访问」标记与「不可达」答案
    if grid[t] == BLOCK:                 # 终点不保证可通行，先挡掉
        sys.stdout.write("-1\n")
        return

    dist[s] = 0                          # 起点即终点时，答案就是这个 0
    q = deque([s])                       # 必须是 deque，list.pop(0) 会 O(n)
    while q:
        u = q.popleft()
        if u == t:
            break                        # 出队即定型，此时 dist[t] 已是最短步数
        d = dist[u] + 1
        # 四个邻居用 ±1、±W 直接算；越界的位置一定落在哨兵墙上，被下面挡住
        for v in (u - W, u + W, u - 1, u + 1):
            if dist[v] < 0 and grid[v] != BLOCK:
                dist[v] = d              # 首次访问即最短，之后不再更新
                q.append(v)
    sys.stdout.write("%d\n" % dist[t])


main()

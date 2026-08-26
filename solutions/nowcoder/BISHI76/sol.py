"""BISHI76 迷宫寻路 —— n*m 网格，问左上角能否走到右下角（四连通，'#' 是墙）。

这题考什么：
    最裸的连通性判定。只问「能不能到」，不问步数，所以 DFS / BFS / 并查集
    都行，本质是一次泛洪填充。

数据规模与复杂度：
    n, m <= 100，格子最多 1e4 个，每格进出各一次，O(nm) 稳过。

Python 的坑（本题必看）：
    递归 DFS 的深度最坏是「整张图是一条蛇形通道」时的 nm = 1e4 层，
    远超 CPython 默认的 1000 层递归上限，而且即使 setrecursionlimit 调大，
    C 栈也可能直接段错误。**所以这里写成显式栈的迭代版**——
    只用一个 list 当栈，push/pop 都是 O(1)，深度完全不受解释器限制。
    （若坚持递归就得 threading.stack_size(1<<26) 起新线程，太重，不值得。）

其它坑：
  1. 起点自己可能就是终点（n = m = 1），这一格出栈时就要判出 Yes，
     若把终点判定写在「扩展邻居时」，1x1 的迷宫会一个邻居都扩展不出来，误答 No；
  2. 「入栈时就标记已访问」而不是「出栈时才标记」：否则同一格会被上下左右
     四个邻居各压一次，栈规模从 O(nm) 膨胀到 O(4nm)，还会重复扩展；
  3. 起点是墙就直接 No。题面保证起点终点是空地，写上这一步不影响正确性，
     换到不保证的数据上也不会走错；
  4. 迷宫每行是一个不含空格的字符串，用 split() 按 token 读正好一行一个 token；
     切出来的是 bytes，g[i][j] 取出的是**整数**，所以要和 ord('#') 比而不是和 '#' 比。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n, m = int(data[0]), int(data[1])
    g = data[2:2 + n]                       # 每行一个 bytes，g[i][j] 是 int

    WALL = ord('#')                         # 与 bytes 里取出的整数比较
    # 起点或终点本身是墙就无从谈起，直接否定
    if g[0][0] == WALL or g[n - 1][m - 1] == WALL:
        sys.stdout.write("No\n")
        return

    vis = [bytearray(m) for _ in range(n)]  # bytearray 比 list of bool 省内存也更快
    vis[0][0] = 1
    stack = [(0, 0)]                        # 显式栈，避免递归深度爆炸
    ok = False
    # 泛洪填充：只关心连通性，出栈顺序无所谓，所以用栈而不是队列
    while stack:
        x, y = stack.pop()
        if x == n - 1 and y == m - 1:       # 出栈时判终点，n=m=1 也能立刻命中
            ok = True
            break                           # 找到即停，剩下的格子不必再走
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < n and 0 <= ny < m and not vis[nx][ny] and g[nx][ny] != WALL:
                vis[nx][ny] = 1             # 入栈即标记，同一格不会被压第二次
                stack.append((nx, ny))
    sys.stdout.write("Yes\n" if ok else "No\n")


main()

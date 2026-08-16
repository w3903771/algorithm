"""BISHI97 旺仔哥哥走迷宫 —— 无向图，只能经过安全房间，问 1 能否到 n。

这题考什么：
    带点权限制的连通性判定。把「有陷阱的房间」直接当作不存在的点删掉，
    剩下的图上做一次 BFS / DFS，看 n 是否可达。

数据规模与复杂度：
    n, m <= 1e5。建邻接表 O(n + m)，一次遍历 O(n + m)。

Python 的坑：
  1. **用 BFS + collections.deque，天然迭代**，不会有递归深度问题
     （这张图可能是一条 1e5 长的链，递归 DFS 必然 RecursionError）；
     deque.popleft 是 O(1)，绝不能用 list.pop(0)；
  2. 邻接表用定长 `[[] for _ in range(n+1)]`，不要 defaultdict(list)——
     1e5 规模下哈希开销明显；
  3. 建表时**顺手过滤掉陷阱点**：只有两端都安全的边才加入，
     这样 BFS 内层循环就不用再判断 t[v]，常数更小。

坑在哪：
  1. **起点 1 自己可能就有陷阱**，此时直接 No（BFS 都不该开始）；
     终点 n 有陷阱同理；
  2. n = 1 时起点即终点，只要 1 号房安全就是 Yes；
  3. 可能有重边、自环，对连通性判定无影响，不必去重。
"""
import sys
from collections import deque


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n, m = int(data[0]), int(data[1])
    trap = data[2:2 + n]                    # b'0' / b'1'
    ONE = b'1'

    if trap[0] == ONE or trap[n - 1] == ONE:   # 起点或终点本身有陷阱
        sys.stdout.write("No\n")
        return

    adj = [[] for _ in range(n + 1)]
    p = 2 + n
    for _ in range(m):
        a = int(data[p]); b = int(data[p + 1]); p += 2
        if trap[a - 1] == ONE or trap[b - 1] == ONE:
            continue                        # 建表时就把陷阱点相关的边扔掉
        adj[a].append(b)
        adj[b].append(a)

    vis = bytearray(n + 1)
    vis[1] = 1
    q = deque([1])
    while q:
        u = q.popleft()
        if u == n:
            sys.stdout.write("Yes\n")
            return
        for v in adj[u]:
            if not vis[v]:
                vis[v] = 1
                q.append(v)
    sys.stdout.write("No\n")        # n == 1 时上面第一轮就命中 u == n 返回 Yes 了


main()

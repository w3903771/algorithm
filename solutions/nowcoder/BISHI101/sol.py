"""BISHI101 世界树上找米库 —— 无根树上，非叶子点中「到最近叶子的距离」最大的那些点。

这题考什么：
    **多源 BFS**。Sekai 点 = 度数为 1 的点（叶子）。
    要对每个非叶子点求「到最近叶子的距离」，逐点单源 BFS 是 O(n^2)，
    正确做法是把**所有叶子同时塞进队列**（距离 0）跑一次 BFS，
    出队顺序保证每个点第一次被访问时拿到的就是到最近叶子的距离。
    最后在非叶子点中取最大值，输出所有取到最大值的编号。

数据规模与复杂度：
    T <= 1e4，Σn <= 2e5。每组 O(n)，总体 O(Σn)。

Python 的坑（本题必看）：
  1. **BFS 天然迭代，队列用 collections.deque**。这棵树可能是一条长链
     （n = 2e5），递归 DFS 会直接撞破递归上限；deque.popleft 是 O(1)；
  2. 邻接表用 CSR（压缩稀疏行：度数前缀和给出每个点的邻居区间，
     所有邻居挤在一个大数组里），不要 defaultdict(list)，
     也不要在多组数据里反复 new 出 2e5 个小 list；
  3. 多组数据的 IO：一次 read().split() 全读进来用游标推进，
     所有输出攒进 list 最后 "\\n".join 一次写出（T 可达 1e4，
     逐组 print 会被 IO 拖垮）。

坑在哪：
  1. n >= 3 保证了树上一定存在非叶子点，不会出现「答案集合为空」；
  2. 叶子点自身 dist = 0，但它们**不参与**最大值的评选（Miku 点不能是 Sekai 点），
     统计最大值时要跳过 deg == 1 的点；
  3. 输出两行：第一行个数，第二行升序编号。按编号从小到大遍历天然有序。

样例复核：
    第二组：叶子 = {1,6,8,9,10}，多源 BFS 得 dist[2]=dist[3]=dist[5]=dist[7]=1，
    dist[4] = 2（邻居 3、5 都是 1）。非叶子中最大是 4 号点的 2，输出 "1\\n4" ✓
"""
import sys
from collections import deque


def main() -> None:
    data = sys.stdin.buffer.read().split()
    ptr = 0
    T = int(data[ptr]); ptr += 1
    out = []
    for _ in range(T):
        n = int(data[ptr]); ptr += 1
        # 边先落到 us / vs 两个数组里，顺手把度数统计出来
        # （度数既用来建 CSR，也用来认叶子，一举两得）
        us = [0] * (n - 1)
        vs = [0] * (n - 1)
        deg = [0] * (n + 2)
        for i in range(n - 1):
            a = int(data[ptr]); b = int(data[ptr + 1]); ptr += 2
            us[i] = a; vs[i] = b
            deg[a] += 1
            deg[b] += 1

        # ---- CSR 邻接表 ----
        # 度数前缀和给出每个点的邻居区间 [start[u], start[u+1])
        start = [0] * (n + 2)
        s = 0
        for i in range(1, n + 1):
            start[i] = s
            s += deg[i]
        start[n + 1] = s            # 末位哨兵，省掉最后一个点的边界特判
        pos = start[:]              # pos[u] = u 的下一个写入位置
        adj = [0] * s
        for i in range(n - 1):
            a = us[i]; b = vs[i]
            adj[pos[a]] = b; pos[a] += 1
            adj[pos[b]] = a; pos[b] += 1   # 无向边两个方向都要存

        # ---- 多源 BFS：所有叶子（Sekai 点）同时入队 ----
        dist = [-1] * (n + 1)       # -1 兼作「尚未访问」的标记
        q = deque()
        for u in range(1, n + 1):
            if deg[u] == 1:         # 度数为 1 即叶子，它到最近叶子的距离是 0
                dist[u] = 0
                q.append(u)
        while q:
            u = q.popleft()
            d = dist[u] + 1         # 队列按层递增，u 出队时 dist[u] 已是最终值
            for i in range(start[u], start[u + 1]):
                v = adj[i]
                if dist[v] < 0:     # 第一次被访问到就是最近的叶子，之后不再更新
                    dist[v] = d
                    q.append(v)

        # ---- 在非叶子点里取最大距离，再收集全部取到它的编号 ----
        best = -1
        for u in range(1, n + 1):
            if deg[u] != 1 and dist[u] > best:   # 只在非叶子里评选
                best = dist[u]
        # 从小到大遍历，结果天然升序，不必再排序
        res = [u for u in range(1, n + 1) if deg[u] != 1 and dist[u] == best]
        out.append(str(len(res)))
        out.append(" ".join(map(str, res)))
    sys.stdout.write("\n".join(out) + "\n")      # T 可达 1e4，攒齐后一次写出


main()

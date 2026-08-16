"""BISHI123 环形字符串跃迁 —— 环上按规则跳 k 次（k <= 1e18），q 次询问终点。

这题考什么：
    1) 先把「一次跃迁」写成一个函数 nxt[i]，问题就变成**函数图（每点出度为 1）上走 k 步**；
    2) 函数图的经典结构：若干个环，环上挂着若干棵内向树。
       走 k 步的答案分两种：
         - 起点在环上：直接 (环内位置 + k) mod 环长；
         - 起点在树上，到环的距离为 d：
             k <= d 时答案是「祖先链上往上第 k 个点」；
             k >  d 时先走 d 步上环，剩下 k-d 步在环上取模。

    为什么不用倍增（binary lifting）？
        倍增是 O((n+q) log k) = 1e5 * 60 * 2 ≈ 1.2e7 次 Python 层循环，
        n=1e5、时限 2 秒下几乎必挂，而且 60 层的 up 表要 6e6 个元素。
    本做法把询问**离线**挂到起点上，一遍 DFS 时用「当前根到当前点的路径栈」
    O(1) 取出第 k 级祖先，总复杂度 **O(n + q)**，没有 log。

    求 nxt：i 后方 m 个字符里最远的 '0'。
        把串**倍长**成长度 2n 的数组 T，预处理 prev0[x] = <= x 的最大的 '0' 下标。
        则 nxt(i) = prev0[i+m] 若它 >= i+1，否则 i+1（都对 n 取模）。O(n)。

数据规模与复杂度：
    n, q <= 1e5，k <= 1e18。时间 O(n + q)，空间 O(n + q)。

坑在哪：
  1. 「最远的一个 0」是**最大**偏移量的 0，不是最近的——读错就全错；
  2. k 可以是 0（原地不动），三种分支都要对 k=0 成立；
  3. 找环用「三色标记 + 路径栈」，注意 path.index(x) 的总代价是 O(n)
     （每个点只会出现在一条路径里），不会退化；
  4. 位置输出是 1-indexed，内部一律 0-indexed，最后 +1。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); m = int(data[1]); q = int(data[2])
    s = data[3]
    ZERO = 48                                # ord('0')

    # ---- 1. 预处理 nxt：倍长串上的「<= x 的最近 0」 ----
    T = s + s                                # 长度 2n，处理环绕
    prev0 = [-1] * (2 * n)
    last = -1
    for x in range(2 * n):
        if T[x] == ZERO:
            last = x
        prev0[x] = last
    nxt = [0] * n
    for i in range(n):
        p = prev0[i + m]
        nxt[i] = p % n if p >= i + 1 else (i + 1) % n

    # ---- 2. 函数图找环：三色标记 ----
    state = [0] * n                          # 0 未访问 / 1 在当前路径上 / 2 已完成
    cyc_id = [-1] * n                        # 属于哪个环（仅环上的点有效）
    cyc_pos = [0] * n                        # 在环中的下标
    cycles = []
    for st0 in range(n):
        if state[st0]:
            continue
        path = []
        x = st0
        while state[x] == 0:
            state[x] = 1
            path.append(x)
            x = nxt[x]
        if state[x] == 1:                    # 撞回本次路径 -> 发现新环
            idx = path.index(x)
            cyc = path[idx:]
            cid = len(cycles)
            cycles.append(cyc)
            for j, v in enumerate(cyc):
                cyc_id[v] = cid
                cyc_pos[v] = j
        for v in path:
            state[v] = 2

    # ---- 3. 询问离线挂到起点 ----
    qs = [[] for _ in range(n)]
    p = 4
    for oi in range(q):
        t = int(data[p]) - 1
        k = int(data[p + 1])
        p += 2
        qs[t].append((k, oi))
    ans = [0] * q

    # 环上的点直接算
    for cyc in cycles:
        L = len(cyc)
        for j, v in enumerate(cyc):
            for k, oi in qs[v]:
                ans[oi] = cyc[(j + k) % L] + 1

    # ---- 4. 树上的点：反向建边后 DFS，用路径栈取第 k 级祖先 ----
    children = [[] for _ in range(n)]
    for v in range(n):
        if cyc_id[v] < 0:                    # v 不在环上，它的父亲是 nxt[v]
            children[nxt[v]].append(v)
    for cyc in cycles:
        L = len(cyc)
        for root in cyc:
            if not children[root]:
                continue
            path = []
            stk = [~root, root]
            while stk:
                v = stk.pop()
                if v < 0:
                    path.pop()
                    continue
                path.append(v)
                d = len(path) - 1            # v 到 root 的距离
                for k, oi in qs[v]:
                    if k <= d:
                        ans[oi] = path[d - k] + 1
                    else:
                        ans[oi] = cyc[(cyc_pos[root] + (k - d)) % L] + 1
                for c in children[v]:
                    stk.append(~c)
                    stk.append(c)
    sys.stdout.write("\n".join(map(str, ans)) + "\n")


main()

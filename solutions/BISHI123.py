"""BISHI123 环形字符串跃迁 —— 环上按规则跳 k 次（k <= 1e18），q 次询问终点。

这题考什么：
    1) 先把「一次跃迁」写成一个函数 nxt[i]，问题就变成**函数图上走 k 步**。
       函数图（functional graph）：每个点恰好有一条出边的有向图，
       因为「下一步去哪」是由当前位置唯一决定的一个函数；
    2) 函数图的经典结构：若干个环，环上挂着若干棵**内向树**
       （树上所有边都朝根的方向，这里的「根」就是环上的那个点）。
       走 k 步的答案分两种：
         - 起点在环上：直接 (环内位置 + k) mod 环长；
         - 起点在树上，到环的距离为 d：
             k <= d 时答案是「祖先链上往上第 k 个点」；
             k >  d 时先走 d 步上环，剩下 k-d 步在环上取模。

    为什么不用倍增（binary lifting）？
        倍增是 O((n+q) log k) = 1e5 * 60 * 2 ≈ 1.2e7 次 Python 层循环，
        n=1e5、时限 2 秒下几乎必挂，而且 60 层的 up 表要 6e6 个元素。
    本做法把询问**离线**处理（先把 q 个询问全部读完、按起点分组存起来，
    再用一遍遍历统一作答；与之相对的「在线」是读一个答一个），
    DFS 时手里正好有一条「当前根到当前点」的路径栈，
    第 k 级祖先就是这个栈从顶往下数第 k 个，O(1) 取出。
    总复杂度 **O(n + q)**，没有 log。

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
    # 把串接一份到自己后面，位置 i 的「后方 m 个字符」就是 [i+1, i+m]，
    # 全落在长度 2n 的数组里，不必写任何环绕取模的分支
    T = s + s                                # 长度 2n，处理环绕
    prev0 = [-1] * (2 * n)
    last = -1                                # -1 表示左边至今没见过 '0'
    for x in range(2 * n):
        if T[x] == ZERO:
            last = x
        prev0[x] = last                      # 下标不超过 x 的最靠右的 '0'
    nxt = [0] * n
    for i in range(n):
        # 「最远的 0」即窗口 [i+1, i+m] 里下标最大的 '0'，
        # 它一定是「不超过 i+m 的最右 '0'」——只要这个位置还在 i+1 之后
        p = prev0[i + m]
        nxt[i] = p % n if p >= i + 1 else (i + 1) % n   # 窗口里没有 0 就只挪一格

    # ---- 2. 函数图找环：三色标记 ----
    # 从每个没走过的点起一路顺着 nxt 走，直到撞上一个已经有颜色的点：
    #   撞到「本次路径上」的点（色 1）说明刚绕出一个新环；
    #   撞到「已完成」的点（色 2）说明这条链汇入了之前找到的环，本次不产生新环。
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
            idx = path.index(x)              # 环从 x 第一次出现的位置开始
            cyc = path[idx:]                 # path 的这个后缀就是整个环
            cid = len(cycles)
            cycles.append(cyc)
            for j, v in enumerate(cyc):
                cyc_id[v] = cid
                cyc_pos[v] = j               # 记下环内序号，之后取模要用
        # 本次路径全部定型；下次再碰到它们就是色 2，不会重复展开，
        # 这也是 path.index 总代价 O(n) 的原因：每个点只进入过一条 path
        for v in path:
            state[v] = 2

    # ---- 3. 询问离线挂到起点 ----
    # qs[t] 收集所有从 t 出发的询问，(步数, 原始编号)；
    # 原始编号保证最后能按输入顺序还原答案
    qs = [[] for _ in range(n)]
    p = 4
    for oi in range(q):
        t = int(data[p]) - 1                 # 题面 1-indexed，内部统一 0-indexed
        k = int(data[p + 1])
        p += 2
        qs[t].append((k, oi))
    ans = [0] * q

    # 环上的点直接算：走 k 步就是环内位置前进 k，对环长取模
    for cyc in cycles:
        L = len(cyc)
        for j, v in enumerate(cyc):
            for k, oi in qs[v]:
                ans[oi] = cyc[(j + k) % L] + 1   # 输出要 1-indexed，故 +1

    # ---- 4. 树上的点：反向建边后 DFS，用路径栈取第 k 级祖先 ----
    # nxt 是「儿子指向父亲」，把它反过来才能自顶向下遍历
    children = [[] for _ in range(n)]
    for v in range(n):
        if cyc_id[v] < 0:                    # v 不在环上，它的父亲是 nxt[v]
            children[nxt[v]].append(v)
    for cyc in cycles:
        L = len(cyc)
        for root in cyc:
            if not children[root]:
                continue                     # 环上这个点没挂树，第 3 步已经答完了
            path = []                        # 从 root 到当前点的路径，path[0] == root
            # 迭代式 DFS：n 可达 1e5，递归会 RecursionError。
            # 每个点压两次——~c 是出栈标记（取反后必为负），
            # 弹到负数就说明这棵子树走完了，该把它从 path 里弹出去
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
                        ans[oi] = path[d - k] + 1        # 还没走出这棵树，第 k 级祖先直接查栈
                    else:
                        # 先花 d 步走到 root（它在环上），剩下 k-d 步在环上绕
                        ans[oi] = cyc[(cyc_pos[root] + (k - d)) % L] + 1
                for c in children[v]:
                    stk.append(~c)           # 先压出栈标记
                    stk.append(c)            # 再压节点本身，保证 c 先被处理
    sys.stdout.write("\n".join(map(str, ans)) + "\n")


main()

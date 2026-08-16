"""BISHI124 【模板】最近公共祖先（LCA）—— N, M <= 5e5 的多叉树 LCA。

这题考什么：
    把 LCA 归约成 **RMQ（区间最小值）**：
      对树做**欧拉序**（DFS 进入/回溯时都记一次，长度 2N-1），
      则 LCA(u, v) = 欧拉序中 [first[u], first[v]] 这一段里**深度最小**的那个点。
      道理很直观：从 u 走到 v 的这段欧拉序必然经过它们的 LCA，
      且不会走到比 LCA 更浅的地方。

    为什么不用倍增？
      倍增建表是 20 层 * 5e5 = 1e7 次赋值，每次询问还要 O(log n) 次跳跃，
      在 Python 里是必挂的量级。欧拉序 + 稀疏表可以做到**查询 O(1)**。

    为什么不用朴素稀疏表？
      2N-1 ≈ 1e6，19 层稀疏表就是 1.9e7 个元素，内存 150MB+ 且建表很慢。
      这里用**分块 + 块间稀疏表**：块长 64，块数 1.6e4，
      稀疏表只有 14 * 1.6e4 ≈ 2e5 个元素；查询时两端零散部分用
      `min(切片)` 在 **C 层**扫最多 64 个元素，中间整块查稀疏表。
      建表和空间都降了两个数量级，查询仍是常数级。

    编码技巧：把 (深度, 结点编号) 压进一个整数 `dep << 20 | node`
    （N <= 5e5 < 2^20），这样可以直接用内置 min 比较，
    取最小值后 & 0xFFFFF 就是 LCA 结点号。区间里深度最小的点唯一（就是 LCA），
    所以不会有并列歧义。

数据规模与复杂度：
    N, M <= 5e5。预处理 O(N)（分块）+ O(nb log nb)，查询 O(1)。

⚠️ Python 现实性判断：**本题在 CPython 3.9 下大概率 TLE**，原因是：
    - 读入 2 * 5e5 + 2 * 5e5 = 2e6 个 token，光 split + int 就要 1s 以上；
    - 建邻接表（CSR）要 ~2e6 次 Python 层循环；
    - 迭代式 DFS 生成欧拉序要 ~1.5e6 次循环迭代；
    - 5e5 次查询，每次约 10 次 Python 层操作 + 2 次 C 层切片 min。
    总量约 6e6~8e6 次 Python 层操作，实测在 8-15 秒量级，
    而时限是「其他语言 6 秒」。这属于**规模对 Python 不友好**，
    做法本身已经是理论最优（O(N) 预处理 + O(1) 查询）；换 PyPy 可过。

坑在哪：
  1. 树是**无根边**给出的（x y 只表示相连），根 R 单独给出，必须迭代式 DFS，
     递归深度可达 5e5，会直接 RecursionError；
  2. 欧拉序长度是 2N-1，first[] 记第一次出现的位置；
  3. 查询时若 first[u] > first[v] 要交换；u == v 时答案是自己（区间退化成一个点，仍正确）；
  4. 邻接表用 CSR（一个扁平数组 + 起止下标）而不是 list of list，
     5e5 个小 list 对象的构造和内存都很贵。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    N = int(data[0]); M = int(data[1]); R = int(data[2])

    # ---- CSR 邻接表：deg 前缀和 + 一次填充 ----
    ne = 2 * (N - 1)
    es = list(map(int, data[3:3 + ne]))      # 只解析一次，别在两个循环里各 int() 一遍
    deg = [0] * (N + 2)
    for x in es:
        deg[x] += 1
    start = [0] * (N + 2)
    acc = 0
    for v in range(1, N + 1):
        start[v] = acc
        acc += deg[v]
    start[N + 1] = acc
    pos = start[:]
    adj = [0] * acc
    for i in range(0, ne, 2):
        x = es[i]; y = es[i + 1]
        adj[pos[x]] = y; pos[x] += 1
        adj[pos[y]] = x; pos[y] += 1

    # ---- 迭代式 DFS 生成欧拉序（值 = dep << 20 | node）----
    par = [0] * (N + 1)
    ptr = start[:]                           # 每个点当前扫到邻接表的哪里
    euler = []
    push = euler.append
    first = [0] * (N + 1)
    dep = 0
    stk = [R]
    par[R] = 0
    first[R] = 0
    push(R)                                  # dep = 0
    while stk:
        u = stk[-1]
        p = ptr[u]
        if p < start[u + 1]:
            ptr[u] = p + 1
            v = adj[p]
            if v != par[u]:
                par[v] = u
                dep += 1
                first[v] = len(euler)
                push((dep << 20) | v)
                stk.append(v)
        else:
            stk.pop()
            dep -= 1
            if stk:
                push(((dep) << 20) | stk[-1])

    L = len(euler)
    # ---- 分块 + 块间稀疏表 ----
    B = 64
    nb = (L + B - 1) // B
    blk = [min(euler[b * B:(b + 1) * B]) for b in range(nb)]
    st = [blk]
    j = 1
    while (1 << j) <= nb:
        prev = st[-1]
        h = 1 << (j - 1)
        st.append(list(map(min, prev, prev[h:])))
        j += 1

    p = 3 + ne
    out = []
    push = out.append
    MASK = (1 << 20) - 1
    for _ in range(M):
        a = int(data[p]); b = int(data[p + 1])
        p += 2
        l = first[a]; r = first[b]
        if l > r:
            l, r = r, l
        bl = l // B
        br = r // B
        if bl == br:
            v = min(euler[l:r + 1])
        else:
            v = min(euler[l:(bl + 1) * B])
            w = min(euler[br * B:r + 1])
            if w < v:
                v = w
            if br - bl > 1:
                k = (br - bl - 1).bit_length() - 1
                row = st[k]
                x = row[bl + 1]
                y = row[br - (1 << k)]
                if x < v:
                    v = x
                if y < v:
                    v = y
        push(v & MASK)
    sys.stdout.write("\n".join(map(str, out)) + "\n")


main()

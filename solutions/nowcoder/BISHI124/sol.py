"""BISHI124 【模板】最近公共祖先（LCA）—— N, M <= 5e5 的多叉树 LCA。

这题考什么：
    把 LCA（Lowest Common Ancestor，最近公共祖先）归约成
    **RMQ（Range Minimum Query，区间最小值查询）**：
      对树做**欧拉序**（Euler tour：DFS 每次进入一个点、以及每次从子树回溯
      回到它时都记一笔，整条序列长 2N-1，相邻两项在树上必是父子关系），
      则 LCA(u, v) = 欧拉序中 [first[u], first[v]] 这一段里**深度最小**的那个点。
      道理很直观：从 u 走到 v 的这段欧拉序必然经过它们的 LCA，
      且不会走到比 LCA 更浅的地方。

    为什么不用倍增？
      倍增（binary lifting，预存每个点向上跳 2^j 步到达谁）建表是
      20 层 * 5e5 = 1e7 次赋值，每次询问还要 O(log n) 次跳跃，
      在 Python 里是必挂的量级。欧拉序 + 稀疏表可以做到**查询 O(1)**。

    为什么不用朴素稀疏表？
      稀疏表（sparse table，也叫 ST 表）：预处理所有「起点任意、长度为 2 的幂」
      的区间最值，查询时用两段可重叠的区间盖住询问区间——最值允许重叠。
      2N-1 ≈ 1e6，19 层稀疏表就是 1.9e7 个元素，内存 150MB+ 且建表很慢。
      这里用**分块 + 块间稀疏表**：块长 64，块数 1.6e4，
      稀疏表只有 14 * 1.6e4 ≈ 2e5 个元素；查询时两端零散部分用
      `min(切片)` 在 **C 层**扫最多 64 个元素，中间整块查稀疏表。
      建表和空间都降了两个数量级，查询仍是常数级。
      见 docs/graph/tree/lca.md 与 docs/basic/binary-lifting.md。

    编码技巧：把 (深度, 结点编号) 压进一个整数 `dep << 20 | node`
    （N <= 5e5 < 2^20），这样可以直接用内置 min 比较，
    取最小值后 & 0xFFFFF 就是 LCA 结点号。区间里深度最小的点唯一（就是 LCA），
    所以不会有并列歧义。

数据规模与复杂度：
    N, M <= 5e5。预处理 O(N)（分块）+ O(nb log nb)，查询 O(1)。

Python 常数账（这题的余量全花在这几处）：
    - 读入 2 * 5e5 + 2 * 5e5 = 2e6 个 token，split 一次读完；
    - 建邻接表（CSR）约 2e6 次 Python 层循环；
    - 迭代式 DFS 生成欧拉序约 1.5e6 次循环迭代；
    - 5e5 次查询，每次约 10 次 Python 层操作 + 2 次 C 层切片 min。
    总量约 6e6~8e6 次 Python 层操作，配「其他语言 6 秒」的时限，
    本文件这份写法在 Python 3 下实测通过。
    这个规模对 Python 并不宽裕，能过靠的是把重活压给 C 层：
    分块把稀疏表缩到 2e5 个元素、零散部分交给内置 min 扫切片、
    (深度, 编号) 压成一个整数从而只比一次。
    做法本身已经是理论最优：O(N) 预处理 + O(1) 查询。

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
    # 树边是无向的，每条边要在两个端点各存一次，所以扁平数组长 2(N-1)
    ne = 2 * (N - 1)
    es = list(map(int, data[3:3 + ne]))      # 只解析一次，别在两个循环里各 int() 一遍
    deg = [0] * (N + 2)
    for x in es:                             # es 里每个端点各出现一次，直接数就是度数
        deg[x] += 1
    start = [0] * (N + 2)                    # start[v] = v 的邻居在 adj 里的起始下标
    acc = 0
    for v in range(1, N + 1):
        start[v] = acc
        acc += deg[v]
    start[N + 1] = acc                       # 末尾哨兵，v 的邻居区间是 [start[v], start[v+1])
    pos = start[:]                           # 填充游标；start 后面还要用，必须复制
    adj = [0] * acc
    for i in range(0, ne, 2):
        x = es[i]; y = es[i + 1]
        adj[pos[x]] = y; pos[x] += 1         # 无向边写两份
        adj[pos[y]] = x; pos[y] += 1

    # ---- 迭代式 DFS 生成欧拉序（值 = dep << 20 | node）----
    # 把 (深度, 编号) 压成一个整数：高位是深度、低 20 位是编号（N < 2^20）。
    # 这样比较大小时深度优先起作用，直接用内置 min 就能取出「最浅的点」，
    # 省掉元组的构造与逐项比较。
    par = [0] * (N + 1)
    ptr = start[:]                           # 每个点当前扫到邻接表的哪里
    euler = []
    push = euler.append
    first = [0] * (N + 1)                    # first[v] = v 在欧拉序中第一次出现的位置
    dep = 0
    stk = [R]                                # 显式栈代替递归：N 可达 5e5，递归必爆栈
    par[R] = 0                               # 根没有父亲，0 不是合法点号，可安全当哨兵
    first[R] = 0
    push(R)                                  # dep = 0，此时 dep << 20 | R 就等于 R
    while stk:
        u = stk[-1]                          # 只看栈顶，不弹出——它的邻居可能还没扫完
        p = ptr[u]
        if p < start[u + 1]:
            ptr[u] = p + 1                   # 游标前进，保证每条边只被检查一次
            v = adj[p]
            if v != par[u]:                  # 跳过回到父亲的那条边，其余邻居都是儿子
                par[v] = u
                dep += 1
                first[v] = len(euler)
                push((dep << 20) | v)        # 进入 v，记一笔
                stk.append(v)
        else:
            # u 的子树走完了，回溯到父亲；欧拉序要在这里补记一次父亲
            stk.pop()
            dep -= 1
            if stk:
                push(((dep) << 20) | stk[-1])

    L = len(euler)                           # 恰好是 2N-1
    # ---- 分块 + 块间稀疏表 ----
    B = 64                                   # 块长；块内零散部分靠 C 层 min 扫，64 是实测折中
    nb = (L + B - 1) // B                    # 块数，向上取整
    blk = [min(euler[b * B:(b + 1) * B]) for b in range(nb)]   # 每块的最小值（末块可能不满，切片自动截断）
    # st[j][b] = 从第 b 块起、连续 2^j 块的最小值
    st = [blk]
    j = 1
    while (1 << j) <= nb:
        prev = st[-1]
        h = 1 << (j - 1)
        # map 遇到较短的迭代器就停，prev 与 prev[h:] 逐项取 min 自动得到正确长度，
        # 整层都在 C 层构建完成，不写一个 Python 层循环体
        st.append(list(map(min, prev, prev[h:])))
        j += 1

    # ---- 回答询问：每次就是欧拉序上的一次区间最小值查询 ----
    p = 3 + ne
    out = []
    push = out.append
    MASK = (1 << 20) - 1                     # 取低 20 位，即还原出结点编号
    for _ in range(M):
        a = int(data[p]); b = int(data[p + 1])
        p += 2
        l = first[a]; r = first[b]
        if l > r:                            # 区间端点无序，先摆正；a == b 时区间退化成一点，仍正确
            l, r = r, l
        bl = l // B                          # 左端点所在块
        br = r // B                          # 右端点所在块
        if bl == br:
            v = min(euler[l:r + 1])          # 同块内，直接 C 层扫最多 64 个元素
        else:
            v = min(euler[l:(bl + 1) * B])   # 左边零散：l 到本块末尾
            w = min(euler[br * B:r + 1])     # 右边零散：右块开头到 r
            if w < v:
                v = w
            if br - bl > 1:                  # 中间还夹着 [bl+1, br-1] 这些整块
                k = (br - bl - 1).bit_length() - 1   # floor(log2(块数))
                row = st[k]
                # 用两段各 2^k 块的区间盖住中间部分，允许重叠——最值可重复贡献
                x = row[bl + 1]
                y = row[br - (1 << k)]
                if x < v:                    # 内联比较，省掉 5e5 次 min() 调用
                    v = x
                if y < v:
                    v = y
        push(v & MASK)                       # 丢掉高位的深度，只留结点编号
    sys.stdout.write("\n".join(map(str, out)) + "\n")


main()

"""BISHI144 食物链计数 —— DAG 上从「入度为 0 的点」到「出度为 0 的点」的路径条数。

这题考什么：
    DAG 上的**路径计数 DP** + 拓扑排序。
        f[x] = 从 x 出发、沿有向边一直走到某个**出度为 0** 的点的路径条数
        f[x] = 1                （x 出度为 0，自己就是一条长度为 0 的链）
        f[x] = Σ_{x -> y} f[y]  （否则）
    答案 = Σ_{入度为 0 的 x} f[x]。

    注意题面文字与样例说明略有出入（说明里把 8 也列成了生产者），
    **以「出度为 0 = 链的一端、入度为 0 = 链的另一端」的形式化定义为准**，
    按样例验算：f(3)=f(5)=1, f(8)=f(9)=f(6)=1, f(2)=2, f(4)=3, f(7)=2, f(10)=4,
    f(1)=2+3+4=9，与期望输出 9 一致。

    实现上按「出度」做 Kahn：先把出度为 0 的点入队，
    出队 v 时把 f[v] 累加给所有 u（u -> v 的前驱），并把 u 的出度减 1，
    减到 0 就入队。这样天然是**逆拓扑序**，不需要显式排序。

数据规模与复杂度：
    n, m <= 1e5，O(n + m)。答案保证 <= 1e9，不需要取模（Python 也不会溢出）。

坑在哪：
  1. **方向别搞反**：输入 `u v` 表示「v 捕食 u」，即有向边 u -> v；
     f 是沿边**正向**走到出度 0 的点的方案数，所以要用**反向邻接表**来递推；
  2. **孤立点不算食物链**。链的定义是「由一条或多条边构成的路径」，
     入度出度都是 0 的点连一条边都没有，不能算一条链。
     不特判的话 f[x] = 1 会被算进答案，n 很大而边很少时会整体偏大；
  3. m 可以为 0；
  4. 迭代式队列，别写递归 DFS（n = 1e5 会爆栈）。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); m = int(data[1])
    es = list(map(int, data[2:2 + 2 * m]))

    # 邻接表用 CSR（压缩稀疏行）：不开 n 个小 list，而是把所有前驱首尾相接放进
    # 一个扁平数组 radj，再用 start 记下每个点那一段的起点，切片即可取用。
    # n, m 到 1e5 时，这样能省掉 1e5 个列表对象的内存与指针开销。
    # 第一遍：数出度、入度，以及每个 v 有多少个前驱
    outdeg = [0] * (n + 1)
    indeg = [0] * (n + 1)
    cnt = [0] * (n + 2)                      # 反向邻接表（按 v 分组存 u）的度数
    for i in range(0, 2 * m, 2):
        u = es[i]; v = es[i + 1]             # 输入 u v 的含义是 v 捕食 u，即有向边 u -> v
        outdeg[u] += 1
        indeg[v] += 1
        cnt[v] += 1
    # 对 cnt 做前缀和得到各段起点，start[n+1] 就是扁平数组的总长度
    start = [0] * (n + 2)
    acc = 0
    for v in range(1, n + 1):
        start[v] = acc
        acc += cnt[v]
    start[n + 1] = acc
    # 第二遍：pos 是各段的写入游标，把每条边填进它归属的那一段
    pos = start[:]
    radj = [0] * acc
    for i in range(0, 2 * m, 2):
        u = es[i]; v = es[i + 1]
        radj[pos[v]] = u                     # v 的前驱里有 u
        pos[v] += 1

    # 孤立点（入度出度都是 0）不构成食物链：链至少要有一条边
    isolated = bytearray(n + 1)
    for x in range(1, n + 1):
        if indeg[x] == 0 and outdeg[x] == 0:
            isolated[x] = 1

    f = [0] * (n + 1)
    # 按「出度」做 Kahn 拓扑：出度为 0 的点先入队，出队顺序天然是逆拓扑序，
    # 轮到 v 时它的所有后继都已结算完，f[v] 已是终值，不必显式排序
    queue = [v for v in range(1, n + 1) if outdeg[v] == 0]
    for v in queue:
        f[v] = 1                             # 出度为 0：自己就是链的起点
    head = 0                                 # 队首游标，queue 同时充当队列与访问序
    while head < len(queue):
        v = queue[head]; head += 1
        fv = f[v]
        for i in range(start[v], start[v + 1]):
            u = radj[i]                      # u -> v，把 v 的方案数并进前驱 u
            f[u] += fv
            outdeg[u] -= 1                   # u 的一条出边结算完毕
            if outdeg[u] == 0:               # 出边全部结算，f[u] 定型，可以入队
                queue.append(u)
    ans = 0
    for x in range(1, n + 1):
        # 链的另一端是入度为 0 的点；孤立点连一条边都没有，不算一条链
        if indeg[x] == 0 and not isolated[x]:
            ans += f[x]
    sys.stdout.write("%d\n" % ans)


main()

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
  2. 孤立点（入度出度都是 0）自成一条链，计入答案 1——公式天然覆盖；
  3. m 可以为 0；
  4. 迭代式队列，别写递归 DFS（n = 1e5 会爆栈）。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); m = int(data[1])
    es = list(map(int, data[2:2 + 2 * m]))

    outdeg = [0] * (n + 1)
    indeg = [0] * (n + 1)
    cnt = [0] * (n + 2)                      # 反向邻接表（按 v 分组存 u）的度数
    for i in range(0, 2 * m, 2):
        u = es[i]; v = es[i + 1]
        outdeg[u] += 1
        indeg[v] += 1
        cnt[v] += 1
    start = [0] * (n + 2)
    acc = 0
    for v in range(1, n + 1):
        start[v] = acc
        acc += cnt[v]
    start[n + 1] = acc
    pos = start[:]
    radj = [0] * acc
    for i in range(0, 2 * m, 2):
        u = es[i]; v = es[i + 1]
        radj[pos[v]] = u                     # v 的前驱里有 u
        pos[v] += 1

    f = [0] * (n + 1)
    queue = [v for v in range(1, n + 1) if outdeg[v] == 0]
    for v in queue:
        f[v] = 1                             # 出度为 0：自己就是链的起点
    head = 0
    while head < len(queue):
        v = queue[head]; head += 1
        fv = f[v]
        for i in range(start[v], start[v + 1]):
            u = radj[i]
            f[u] += fv
            outdeg[u] -= 1
            if outdeg[u] == 0:
                queue.append(u)
    ans = 0
    for x in range(1, n + 1):
        if indeg[x] == 0:
            ans += f[x]
    sys.stdout.write("%d\n" % ans)


main()

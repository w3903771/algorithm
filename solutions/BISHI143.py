"""BISHI143 没有上司的舞会 —— 树上最大权独立集（选了某点就不能选它的父亲）。

这题考什么：
    最经典的**树形 DP**，两个状态：
        g[u] = 邀请 u 时，u 的子树能达到的最大气氛值
             = w_u + Σ_{c 是 u 的孩子} f[c]           （孩子一律不能选）
        f[u] = 不邀请 u 时的最大值
             = Σ_c max(g[c], f[c])                    （孩子随意）
    答案 = max(g[root], f[root])。

⚠️ Python 关键：**必须用迭代式后序遍历**。
    n <= 2e5，链状数据下递归深度就是 2e5，直接 RecursionError；
    即使 setrecursionlimit 调大，CPython 也会爆 C 栈段错误。
    两种正确姿势：
      1. 显式栈的迭代式 DFS（本文件采用）；
      2. threading.stack_size(1<<26) + 新线程里跑递归。
    本题的输入天然给出「k 是 ℓ 的上司」的**有向父子边**，
    所以连 DFS 都可以省掉：只要按 BFS 序遍历一遍，再**倒着**累加即可
    ——子节点一定排在父节点后面，倒序就是合法的后序。

数据规模与复杂度：
    n <= 2e5，O(n) 时间、O(n) 空间。

坑在哪：
  1. **w_i 可以是负数**（-128..127），所以 g[u] 不一定优于 f[u]，
     不能写成「叶子一定选」的贪心；
  2. 根不是 1，而是「没有出现在 ℓ 位置上的那个点」，要找出来；
  3. 只有 n-1 条边、且给的是有向父子关系，不需要判重边/无向边；
  4. 累加用 f、g 两个数组直接「加到父亲身上」，比建结果列表再求和快。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    w = [0] * (n + 1)
    for i in range(1, n + 1):
        w[i] = int(data[i])

    # ---- CSR 建孩子表 + 找根 ----
    deg = [0] * (n + 2)
    par = [0] * (n + 1)
    es = list(map(int, data[n + 1:n + 1 + 2 * (n - 1)]))
    for i in range(0, len(es), 2):
        k = es[i]; l = es[i + 1]
        deg[k] += 1
        par[l] = k
    start = [0] * (n + 2)
    acc = 0
    for v in range(1, n + 1):
        start[v] = acc
        acc += deg[v]
    start[n + 1] = acc
    pos = start[:]
    ch = [0] * acc
    for i in range(0, len(es), 2):
        k = es[i]
        ch[pos[k]] = es[i + 1]
        pos[k] += 1
    root = 1
    for v in range(1, n + 1):
        if par[v] == 0:
            root = v
            break

    # ---- BFS 序（父亲一定排在孩子前面），再倒着累加 = 后序 DP ----
    order = [root]
    head = 0
    while head < len(order):
        u = order[head]; head += 1
        order.extend(ch[start[u]:start[u + 1]])

    g = w[:]                                 # g[u] 初值 = w_u
    f = [0] * (n + 1)                        # f[u] 初值 = 0
    for i in range(len(order) - 1, 0, -1):   # 跳过下标 0（根），倒序即后序
        u = order[i]
        p = par[u]
        gu = g[u]; fu = f[u]
        g[p] += fu                           # 选了 p 就不能选 u
        f[p] += gu if gu > fu else fu        # 不选 p，u 随意
    sys.stdout.write("%d\n" % (g[root] if g[root] > f[root] else f[root]))


main()

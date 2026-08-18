"""BISHI142 最大学分 —— 选恰好 M 门课，选一门必须选它的全部先修课，求最大学分。

这题考什么：
    **树形背包**（依赖背包）。每门课至多一个直接先修课 ⇒ 先修关系构成森林；
    加一个编号 0 的**虚拟根**（学分 0）把森林接成一棵树，问题变成
    「在树上选 M+1 个点（含虚拟根），且选中的点集**对父亲封闭**，求最大权和」。

        f[u][j] = 在 u 的子树里选 j 个点、且 **u 必被选中**（j >= 1）时的最大学分
        f[u][0] = 0
        初值 f[u][1] = s_u，然后逐个合并孩子：
            f[u][j] = max_{t=0..j-1} ( f[u][j-t] + f[c][t] )
    合并时「先复制一份旧的 f[u] 再倒着更新」，本质上就是**分组背包**：
    每个孩子是一组，组内选项是「从这个孩子的子树里拿 t 个点」。

    复杂度：经典结论是「每对点只会在它们的 LCA 处被合并一次」，
    所以总合并量是 O(N^2)（在 M 的截断下更小），N = 300 时不到 9e4。

数据规模与复杂度：
    N, M <= 300，O(N·M) ~ O(N^2) = 9e4，随便跑。

坑在哪：
  1. **要选的是「恰好 M 门」**，加虚拟根后目标变成 f[0][M+1]（虚拟根占一个名额）；
  2. 合并时 t 的上界要同时受「孩子子树大小」和「M+1」两个约束截断，
     不截断会退化成 O(N·M^2)（本题也能过，但养成好习惯）；
  3. 先修关系可能形成很深的链（深度到 300），
     这里用**迭代式后序遍历**，不依赖递归（递归 300 层虽然安全，但迭代是通用姿势）；
  4. 学分 s_i >= 1，所以选得越多越好——但名额恰好 M，别写成「至多 M」。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    N = int(data[0]); M = int(data[1])
    s = [0] * (N + 1)
    # 下标 0 是虚拟根：学分 0，所有「无先修课」的课程都挂到它下面，
    # 森林由此接成一棵树，全局只剩一个入口
    children = [[] for _ in range(N + 1)]
    for i in range(1, N + 1):
        k = int(data[2 * i]); s[i] = int(data[2 * i + 1])
        children[k].append(i)                # k = 0 表示挂到虚拟根
    cap = M + 1                              # 含虚拟根一共要选 M+1 个点

    # ---- 迭代式后序遍历：先拿到处理顺序，再倒着做 DP ----
    # 先修链最深可到 300 层，用显式栈代替递归，深度再大也不会爆栈
    order = []
    stk = [0]
    while stk:
        u = stk.pop()
        order.append(u)
        stk.extend(children[u])

    NEG = -(1 << 60)                         # 「这个点数凑不出来」的哨兵
    f = [None] * (N + 1)
    for u in reversed(order):                # 保证孩子先于父亲被处理
        cur = [0, s[u]]                      # f[u][0]=0, f[u][1]=s_u
        for c in children[u]:                # 每个孩子是分组背包里的一「组」
            fc = f[c]
            f[c] = None                      # 及时释放
            lc = len(fc)
            nl = len(cur) + lc - 1           # 合并后能取到的点数上限
            if nl > cap:                     # 超过 M+1 的部分再也用不上，截断
                nl = cap + 1                 # 这一步把复杂度从 O(N·M^2) 压回 O(N·M)
            new = [NEG] * nl
            new[0] = 0                       # 一个点都不取时学分为 0，与 u 是否被选无关
            for j in range(1, nl):           # 分组背包：这个孩子取 t 个点
                best = NEG
                lo = j - (len(cur) - 1)      # cur 侧最多只有 len(cur)-1 个点可分
                if lo < 0:
                    lo = 0
                hi = lc - 1                  # 孩子子树里最多能取这么多点
                if hi > j - 1:               # u 自己必占一个名额，所以 t 至多 j-1
                    hi = j - 1
                for t in range(lo, hi + 1):
                    v = cur[j - t] + fc[t]
                    if v > best:
                        best = v
                new[j] = best
            cur = new
        f[u] = cur
    root = f[0]
    # cap 超出树能提供的点数时（M 比课程总数还大）根本无解，按 0 输出
    sys.stdout.write("%d\n" % (root[cap] if cap < len(root) else 0))


main()

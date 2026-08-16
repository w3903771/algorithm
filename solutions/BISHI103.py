"""BISHI103 【模板】有依赖的背包问题 —— 云朵成组捆绑销售（洛谷 P1455 搭配购买）。

这题考什么：
    题面说「买 u 必须买 v，买 v 也必须买 u」——这是**双向**依赖，
    于是「必须一起买」的关系是等价关系，用**并查集**把互相牵连的云朵缩成一个
    「超级物品」（价格 = 组内价格之和，价值 = 组内价值之和）。
    缩完之后就是一个最普通的 **0/1 背包**：每个组要么整组买、要么不买。

    （注意区分：真正的「树形依赖背包」是单向依赖（买子必须买父），
      那才需要树上分组背包；本题是双向，缩点后退化成裸 0/1 背包。）

数据规模与复杂度：
    n <= 1e4 朵云、m <= 5e3 个搭配、w <= 1e4 元。
    并查集 O((n+m)α)，背包最坏 O(组数 * w) = 1e8——这在 C++ 里刚好，
    在 Python 里逐格 for 循环是绝对跑不动的。

Python 的关键优化（本题的核心）：
  1. **用整段切片 + map(max, ...) 代替内层 for**：
        dp[c:hi+1] = list(map(max, dp[c:hi+1], [x + v for x in dp[:hi-c+1]]))
     这样内层循环全部下沉到 C 层，比 Python 级的 `for j in range(w, c-1, -1)`
     快一个数量级以上。注意 0/1 背包必须「用旧的 dp 去更新新的 dp」，
     切片天然复制了一份旧值，所以不会出现完全背包那样的重复选取；
  2. **上界收缩 reach**：处理到第 k 个组时，能凑出的总花费不会超过
     前 k 个组的价格之和，所以只需要更新 dp[c .. min(w, 前缀和)]。
     在「大量廉价小组」的数据下这能把工作量直接砍掉一半以上；
  3. 价格超过 w 的组直接跳过。

坑在哪：
  1. 输入第一行是 n, m, w 三个数（题面把 w 写在括号外面，容易看漏）；
  2. 并查集的 find 要写**迭代**路径压缩，1e4 规模虽不至于爆栈，
     但保持习惯，也更快；
  3. 答案取 dp[w]（而不是 max(dp)）即可，因为 dp 数组本身是「容量 <= j」
     的非降形式吗？——不是，这里 dp[j] 是「恰好用 j」的松弛式写法，
     由于我们从 dp 全 0 开始且允许不装满，dp[j] 实际含义是「容量 j 的最优值」，
     单调不降，取 dp[w] 正确。

样例复核：
    5 朵云 (3,10)(3,10)(3,10)(5,100)(10,1)，搭配 1-3、3-2、4-2 -> {1,2,3,4} 一组，
    价格 3+3+3+5 = 14 > 10 买不起；{5} 组价格 10、价值 1。答案 1 ✓
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); m = int(data[1]); w = int(data[2])

    cost = [0] * (n + 1)
    val = [0] * (n + 1)
    p = 3
    for i in range(1, n + 1):
        cost[i] = int(data[p]); val[i] = int(data[p + 1]); p += 2

    parent = list(range(n + 1))

    def find(x: int) -> int:
        r = x
        while parent[r] != r:
            r = parent[r]
        while parent[x] != r:                 # 迭代路径压缩
            parent[x], x = r, parent[x]
        return r

    for _ in range(m):
        u = int(data[p]); v = int(data[p + 1]); p += 2
        ru, rv = find(u), find(v)
        if ru != rv:
            parent[ru] = rv

    # 缩点：同一集合的云朵合成一个「超级物品」
    gc = [0] * (n + 1)
    gv = [0] * (n + 1)
    for i in range(1, n + 1):
        r = find(i)
        gc[r] += cost[i]
        gv[r] += val[i]

    dp = [0] * (w + 1)
    reach = 0                                  # 目前所有已处理组的价格之和（上限 w）
    for i in range(1, n + 1):
        if parent[i] != i or gc[i] > w:        # 只处理代表元，且买得起的
            continue
        c = gc[i]; v = gv[i]
        reach += c
        if reach > w:
            reach = w
        hi = reach
        # 0/1 背包：dp[j] = max(dp[j], dp[j-c] + v)，整段切片交给 C 层
        dp[c:hi + 1] = list(map(max, dp[c:hi + 1],
                                [x + v for x in dp[:hi - c + 1]]))
    sys.stdout.write("%d\n" % dp[w])


main()

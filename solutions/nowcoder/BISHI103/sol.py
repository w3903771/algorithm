"""BISHI103 【模板】有依赖的背包问题 —— 云朵成组捆绑销售（洛谷 P1455 搭配购买）。

这题考什么：
    题面说「买 u 必须买 v，买 v 也必须买 u」——这是**双向**依赖，
    于是「必须一起买」的关系是等价关系，用**并查集**把互相牵连的云朵缩成一个
    「超级物品」（价格 = 组内价格之和，价值 = 组内价值之和）。
    缩完之后就是一个最普通的 **0/1 背包**：每个组要么整组买、要么不买。
    并查集见 docs/ds/dsu.md，
    0/1 背包与二进制拆分见 docs/dp/knapsack.md。

    （注意区分：真正的「树形依赖背包」是单向依赖（买子必须买父），
      那才需要树上分组背包；本题是双向，缩点后退化成裸 0/1 背包。）

数据规模与复杂度：
    n <= 1e4 朵云、m <= 5e3 个搭配、w <= 1e4 元。
    并查集 O((n+m)α)，背包最坏 O(组数 * w) = 1e8——这在 C++ 里刚好，
    在 Python 里逐格 for 循环是绝对跑不动的，必须把内层循环下沉到 C 层。

Python 的关键优化（本题的核心，四条一起上）：
  1. **用整段切片 + zip 列表推导代替内层 for**：
        shifted = [x + v for x in dp[:reach+1-c]]
        dp[c:reach+1] = [a if a > b else b for a, b in zip(dp[c:reach+1], shifted)]
     内层循环全部走 C 层的切片 / zip / 列表推导，比 Python 级的
     `for j in range(w, c-1, -1)` 快一个数量级以上。
     注意 0/1 背包必须「用旧的 dp 去更新新的 dp」，
     切片天然复制了一份旧值，所以不会出现完全背包那样的重复选取；
  2. **同价剪枝 + 相同 (价格, 价值) 去重 + 二进制拆分**：
     - 价格为 c 的组最多只能买 w//c 个，按交换论证只保留价值最大的那 w//c 个；
     - 把 k 个完全一样的组合成 1, 2, 4, ..., 剩余 这 O(log k) 个「打包物品」。
       这不改变可达的方案集合（任意 0..k 个都能被这些幂次凑出），
       却能把「大量廉价同款小组」这种最容易卡人的数据从 1e4 件压到几十件；
  3. **按价格升序处理 + dp 数组按 reach 动态增长**：处理完前 k 件后，
     能花出去的钱不会超过这 k 件的价格之和 reach = min(w, Σc)，
     容量再大也只是同一个答案。于是让 dp 的长度始终只有 reach+1，
     每引入一件新物品就用 dp[-1]（即 dp[reach]）把数组扩展到新的 reach。
     **按价格升序**能让 reach 增长得最慢，把总工作量的上界从 组数*w
     压到 Σ_k min(前 k 件价格和, w) <= w^2/2 ≈ 5e7。
     最后答案取 dp[reach]——reach < w 时说明全部组都买得起，dp[reach] 就是总价值。
     **注意**：不能只把更新范围截断到 reach 却仍然读 dp[w]——
     那样 dp[reach+1..w] 会残留旧值（本该继承 dp[reach]），答案会偏小。
     这是这个优化最容易写错的地方，必须真的把数组扩展并填上继承值；
  4. 价格超过 w 的组（以及拆分后价格超过 w 的打包物品）直接跳过。

    即便如此，「1e4 个价格各异的组 + w = 1e4」这类极限数据仍要做约 5e7 次
    元素级运算。这是 CPython 的物理下限，超出本题留给其他语言的 2 秒。
    因此本题按 **PyPy3** 提交：同一份代码在 PyPy3 的即时编译下，
    这段元素级循环会被编译成机器码，时间落回限制之内。
    上面四条优化在 PyPy3 下同样不能省——少了它们，工作量会回到
    组数 * w = 1e8，PyPy3 也追不回来。

坑在哪：
  1. 输入第一行是 n, m, w 三个数（题面把 w 写在括号外面，容易看漏）；
  2. 并查集的 find 要写**迭代**路径压缩，1e4 规模虽不至于爆栈，
     但保持习惯，也更快；
  3. 依赖是**双向**的（买 u 必买 v，买 v 也必买 u），所以是并查集缩点，
     不要误当成树形依赖背包。

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

    # 每条搭配关系都是双向的，直接把两端并进同一个集合
    for _ in range(m):
        u = int(data[p]); v = int(data[p + 1]); p += 2
        ru, rv = find(u), find(v)
        if ru != rv:
            parent[ru] = rv

    # 缩点：同一集合的云朵合成一个「超级物品」
    gc = [0] * (n + 1)                        # gc / gv 只在代表元下标上有意义
    gv = [0] * (n + 1)
    for i in range(1, n + 1):
        r = find(i)                           # 把每朵云的价格与价值累加到它的代表元
        gc[r] += cost[i]
        gv[r] += val[i]

    # 按价格分桶。价格为 c 的组最多只能买 w//c 个，
    # 由交换论证，留下价值最大的那 w//c 个就够了，其余永远用不上。
    by_cost = {}
    for i in range(1, n + 1):
        if parent[i] != i or gc[i] > w:        # 只处理代表元，且买得起的
            continue
        by_cost.setdefault(gc[i], []).append(gv[i])

    # 剪完之后再把相同 (价格, 价值) 的组合并计数，做二进制拆分
    bag = {}
    for c, vals in by_cost.items():
        keep = w // c
        if len(vals) > keep:
            vals.sort(reverse=True)
            del vals[keep:]
        for v in vals:
            key = (c, v)
            bag[key] = bag.get(key, 0) + 1

    items = []
    for (c, v), k in bag.items():
        step = 1                               # 打包份额依次取 1, 2, 4, ...
        while k:
            take = step if step <= k else k    # 最后一份取剩余量，保证总和恰为 k
            cc = c * take
            if cc <= w:                        # 打包后超预算的直接丢掉
                items.append((cc, v * take))
            k -= take
            step <<= 1                         # 份额翻倍，总份数只有 O(log k)
    items.sort()                               # 价格升序，让 reach 涨得最慢

    dp = [0]                                   # dp[j] 只维护 j = 0..reach
    reach = 0                                  # 已处理物品的价格之和（上限 w）
    for c, v in items:
        nr = reach + c                         # 加入这一件后，钱最多能花到 nr
        if nr > w:
            nr = w                             # 预算封顶，再多也花不出去
        if nr > reach:
            dp.extend([dp[-1]] * (nr - reach))  # 新容量继承 dp[reach]（钱花不完）
            reach = nr
        # 0/1 背包：dp[j] = max(dp[j], dp[j-c] + v)，整段切片把内层循环交给 C 层
        # shifted 的第 j-c 项就是 dp[j-c] + v，切片已复制旧值，故不会重复选取
        shifted = [x + v for x in dp[:reach + 1 - c]]
        dp[c:reach + 1] = [a if a > b else b
                           for a, b in zip(dp[c:reach + 1], shifted)]
    sys.stdout.write("%d\n" % dp[reach])       # reach 即实际能花出去的钱的上限


main()

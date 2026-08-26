"""BISHI147 旅行者的大逃脱 —— 带时刻约束的网格路径计数 + 最短时刻。

⚠️ **本题必须用 PyPy3 提交**（牛客语言 id 25），CPython 交不过去。原因见文末。

这题考什么：
    时间维 DP（分层图 DP）+ 前缀和优化。每个时刻只能「向下或向右走任意正整数步」，
    检查官从某时刻起永久占据格子，路径的每一次「离开/经过/到达」都受时刻约束。

时刻语义（题面表述含糊，下面这套读法由样例 1 的两组数据唯一确定）：
    记路径的停留点为 p_1=(1,1), p_2, ..., p_{T+1}=(n,m)，第 j 次移动发生在时刻 j。
    对每个格子取 block[c] = 占据它的检查官中最早的时刻（无人则 +inf），则合法条件是：

        对每个 j = 1..T，半开区间 [p_j, p_{j+1}) 上所有格子都满足 block > j

    也就是「出发格 + 途经格」受时刻 j 约束，而**到达格不在此列**——
    因为到达格会在下一时刻作为出发格被检查（约束 block > j+1，更强），
    唯一例外是终点 (n,m)，它不再出发，而题目保证它永不被占据。

    样例 1 的两组数据都只有路径 (1,1)→(2,1)→(2,3)（第二步跨过 (2,2)）有希望：
      · block[(2,2)] = 3 时，跨过发生在时刻 2 < 3，合法 ⇒ 1 条路径、最短时刻 2；
      · block[(2,2)] = 2 时，时刻 2 已被占据 ⇒ 无解。
    而 (1,1)→(2,1)→(2,2)→(2,3) 这条在两组里都非法：停在 (2,2)，
    时刻 3 离开时 block ≤ 3，必被捕获。这恰好排除了「到达格也受时刻 j 约束」的读法。

算法：
    dp[j][c] = 时刻 j 站在格子 c 的方案数（即已走 j-1 步）。
    转移时先把 block == j 的格子置为不可通行，再在每一行/每一列内做
    「带重置的前缀和」——因为一次移动必须落在同一段连续可通行区间内。
    到达终点即逃脱，故转移后要把终点的 dp 清零，避免它继续出发。

    答案：方案数 = Σ_{T=1..k} dp[T+1][终点]，最短时刻 = 最小的这种 T。

前缀和优化的写法：
    dp 用**一维扁平数组**存，这样
      · 第 x 行是 dp[x*m : (x+1)*m]      —— 连续切片
      · 第 y 列是 dp[y::m]               —— 步长切片
    两者都能直接喂给 itertools.accumulate，把内层循环压进 C 层。
    又因为 q ≤ 100，被占据的格子最多 100 个，绝大多数行/列只有一整段可通行区间，
    accumulate 一次就够；只有含被占格的行列才需要按段处理。
    可通行区间用 row_runs / col_runs 缓存，某格被占时只重算它所在的那一行一列。

坑在哪：
    1. 到达终点后必须停下，dp[终点] 要清零，否则会把「经过终点再继续走」也算进去；
    2. 到达一个已被占据的格子是死状态（下一时刻离开必被捕），可以直接丢弃，
       所以转移时出发格与到达格都限制在同一段可通行区间内；
    3. block 取同格多名检查官的**最小**时刻（题面明说可能多人同格）；
    4. 输出顺序是「方案数 最短时刻」，不是「最短时刻 方案数」。

数据规模与复杂度：
    T <= 5 组，n, m <= 500，q <= 100，k <= 100，时限「其他语言 4 秒」。
    状态数 k·n·m = 100·500·500 = 2.5e7，每组都要跑满，五组合计 1.25e8 个状态。
    前缀和把每个时刻的转移压到 O(nm) 的 C 层操作，这已是本题的复杂度下界。

为什么必须 PyPy3：
    即使把前缀和压进 C 层，每个时刻仍要对 250000 个元素做一次 Python 层取模，
    每组数据还有 k·(n+m) = 1e5 次 Python 层的切片调用。
    极限数据（T=5、n=m=500、k=100、q=100）在 CPython 下实测 30.8 秒，
    同样思路的 C++ 实现约 0.3 秒。这不是实现没优化到位，而是 2.5e7 量级的
    状态转移在纯 CPython 里的物理下限；PyPy3 的 JIT 能把这些循环编译成机器码。
    识别信号：状态数上千万 + 转移带取模 + 无法整体向量化。
    详见 docs/appendix/c-pitfalls.md 的「Python 打不过的题型」一节。
"""
import sys
from itertools import accumulate
from operator import add

MOD = 998244353


def solve(n, m, k, inspectors):
    nm = n * m
    target = nm - 1                       # (n,m) 的扁平下标
    big = k + 1                           # 只要 > k 就等价于「永不被占据」

    # block[p]：占据格子 p 的检查官中最早的时刻
    block = [big] * nm
    for x, y, t in inspectors:
        p = (x - 1) * m + (y - 1)
        if t < block[p]:
            block[p] = t
    # 按时刻分桶，转移前逐时刻「熄灭」格子。
    # 这样整个过程只需单向地把格子从可通行改成不可通行，不必每个时刻重扫全图
    newly = [[] for _ in range(k + 2)]
    for p, t in enumerate(block):
        if t <= k:
            newly[t].append(p)

    passable = bytearray([1]) * nm        # 1 = 当前时刻该格仍可通行

    def build_row(x):
        """扫出第 x 行的可通行连续段，每段是左闭右开的列区间 [s, e)。"""
        base = x * m
        runs, s = [], -1                  # s = 当前段的起点，-1 表示还没开段
        for y in range(m):
            if passable[base + y]:
                if s < 0:
                    s = y
            elif s >= 0:                  # 撞到墙，收尾当前段
                runs.append((s, y))
                s = -1
        if s >= 0:                        # 扫到行尾还开着段，补上
            runs.append((s, m))
        return runs

    def build_col(y):
        """扫出第 y 列的可通行连续段，每段是左闭右开的行区间 [s, e)。"""
        runs, s = [], -1
        for x in range(n):
            if passable[x * m + y]:
                if s < 0:
                    s = x
            elif s >= 0:
                runs.append((s, x))
                s = -1
        if s >= 0:
            runs.append((s, n))
        return runs

    # 一次移动必须整段落在同一个可通行区间里（途中任一格被占就会被捕），
    # 所以先把每行每列切成若干段，前缀和只在段内累加
    row_runs = [build_row(x) for x in range(n)]
    col_runs = [build_col(y) for y in range(m)]

    dp = [0] * nm                         # dp[c] = 当前时刻站在格子 c 的方案数
    dp[0] = 1                             # 时刻 1 站在 (1,1)
    count = 0                             # 累计逃脱方案数
    best = -1                             # 最短时刻，-1 表示还没成功过

    for j in range(1, k + 1):
        # 时刻 j 起，block == j 的格子不可通行
        for p in newly[j]:
            if passable[p]:
                passable[p] = 0
                # q <= 100，被占格子最多 100 个，只重建它所在的那一行一列即可
                row_runs[p // m] = build_row(p // m)
                col_runs[p % m] = build_col(p % m)

        nxt = [0] * nm

        # 向右：行内前缀和。走任意正整数步 = 落点的方案数是它左边同段各格之和
        for x in range(n):
            base = x * m
            for s, e in row_runs[x]:
                span = e - s
                if span < 2:              # 段里只有一格，右移无处可去
                    continue
                acc = list(accumulate(dp[base + s:base + e]))
                # 落点从 s+1 起，acc[:span-1] 正好是「落点左侧（含出发格）之和」，
                # 错开一位就实现了「至少走一步」
                lo, hi = base + s + 1, base + e
                nxt[lo:hi] = list(map(add, nxt[lo:hi], acc[:span - 1]))

        # 向下：列内前缀和（步长切片，同样落到 C 层）
        for y in range(m):
            runs = col_runs[y]
            if not runs:                  # 整列都被占，跳过
                continue
            col = dp[y::m]                # 扁平存储让「第 y 列」也是一次切片
            for s, e in runs:
                span = e - s
                if span < 2:
                    continue
                acc = list(accumulate(col[s:e]))
                lo = (s + 1) * m + y      # 第 s+1 行第 y 列的扁平下标
                hi = (e - 1) * m + y + 1  # 右开，+1 是为了让步长切片取到第 e-1 行
                nxt[lo:hi:m] = list(map(add, nxt[lo:hi:m], acc[:span - 1]))

        # nxt 现在是「时刻 j+1 站在各格」的方案数
        arrived = nxt[target] % MOD
        if arrived:
            count = (count + arrived) % MOD
            if best < 0:                  # j 递增，第一次到达即最短时刻
                best = j
        nxt[target] = 0                   # 到达终点即逃脱，不再出发

        dp = [v % MOD for v in nxt]       # 前缀和过程中不取模，一个时刻收一次

    return (count, best) if best >= 0 else None


def main():
    data = sys.stdin.buffer.read().split()
    p = 0
    T = int(data[p]); p += 1
    out = []
    for _ in range(T):
        n, m, q, k = (int(data[p]), int(data[p + 1]),
                      int(data[p + 2]), int(data[p + 3]))
        p += 4
        insp = []
        for _ in range(q):
            insp.append((int(data[p]), int(data[p + 1]), int(data[p + 2])))
            p += 3
        res = solve(n, m, k, insp)
        out.append("-1" if res is None else "{} {}".format(res[0], res[1]))
    sys.stdout.write("\n".join(out) + "\n")


main()

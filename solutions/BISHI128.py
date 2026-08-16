"""BISHI128 区间加乘与单点求值 —— 区间加 x、区间乘 x、单点查询 mod 998244353。

这题考什么：
    1) **仿射变换的复合**：加和乘都是 x -> k·x + b 的特例，两个变换复合成
           (k1, b1) 然后 (k2, b2)  ==>  (k1·k2,  b1·k2 + b2)
       「先加 1 再乘 2」在 x=0 处得 2，「先乘 2 再加 1」得 1——**顺序绝不能反**，
       这是双标记题的头号 WA 来源。
    2) **离线换维**：本题只有**单点查询**，这给了在线线段树之外的第二条路。

    在线做法（区间仿射 + 单点查的懒标记线段树）每次修改要沿两条边界路径 push down，
    约 200-300 次 Python 层操作，1e5 次修改就是 3e7 —— Python 下没戏。

    本解法把维度换过来：
      - **扫描轴 = 下标 i**（从 1 到 n）；
      - 建一棵以**操作时间**为下标的线段树，叶子 j 存第 j 个修改操作的仿射变换，
        未覆盖当前下标时是恒等 (1, 0)；内部节点 = 左右儿子按时间顺序的复合；
      - 操作 (l, r, k, b) 在 i = l 处「激活」（写入叶子），在 i = r+1 处「失效」（写回恒等）——
        每个操作只做 **2 次单点修改**；
      - 查询 (下标 x, 该查询之前有 T 个修改) 时，取时间前缀 [0, T) 的复合，
        作用在 a_x 上即可。
    每次单点修改 O(log q)，每次查询 O(log q)，总量约 3q·log q ≈ 5e6 次迭代。

数据规模与复杂度：
    n, q <= 1e5。时间 O((n + q) log q)，空间 O(n + q)。

⚠️ Python 现实性判断：**在 CPython 3.9 下大概率 TLE**，原因是：
    时限只有「其他语言 2 秒」，而本做法约需 5e6 次 Python 层循环迭代
    （每次迭代含 2 次模乘），实测在 3-5 秒量级。
    但它已经比在线线段树快 3-5 倍，是本题在 Python 下最有希望的写法；PyPy 下可过。

坑在哪：
  1. **复合顺序**：新操作作用在旧结果**之后**，所以 b <- b·k_new + b_new；
  2. a_i 和 x 都可能是负数，先 % MOD 化到 [0, MOD)（Python 的 % 对负数返回非负，省心）；
  3. 查询取的是**时间前缀** [0, T)，不是整棵树的根——
     根含有比该查询更晚的操作，直接读根是错的；
  4. 若一个修改也没有（全是查询），线段树要能退化到「只有一个恒等叶子」。
"""
import sys

MOD = 998244353


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); q = int(data[1])
    a = [0] + [int(v) % MOD for v in data[2:2 + n]]

    # ---- 先把所有操作读进来，按下标挂事件 ----
    act = [[] for _ in range(n + 2)]         # 在下标 i 处激活的修改编号
    dea = [[] for _ in range(n + 2)]         # 在下标 i 处失效的修改编号
    qs = [[] for _ in range(n + 2)]          # 下标 i 上的查询：(此前修改数 T, 输出序号)
    ops = []                                 # 第 j 个修改的 (k, b)
    p = 2 + n
    nq = 0
    for _ in range(q):
        op = data[p]
        if op == b"3":
            x = int(data[p + 1]); p += 2
            qs[x].append((len(ops), nq))
            nq += 1
        else:
            l = int(data[p + 1]); r = int(data[p + 2]); v = int(data[p + 3]) % MOD
            p += 4
            j = len(ops)
            ops.append((1, v) if op == b"1" else (v, 0))
            act[l].append(j)
            dea[r + 1].append(j)

    # ---- 时间轴线段树：叶子存仿射变换，内部节点存「左儿子 then 右儿子」的复合 ----
    size = 1
    while size < max(1, len(ops)):
        size <<= 1
    km = [1] * (2 * size)                    # 乘法系数
    kb = [0] * (2 * size)                    # 加法系数

    def assign(j, k, b):
        """把叶子 j 设为 (k, b)，并沿路更新祖先，O(log q)。"""
        i = j + size
        km[i] = k; kb[i] = b
        i >>= 1
        while i:
            lc = i << 1; rc = lc | 1
            kr = km[rc]
            km[i] = km[lc] * kr % MOD
            kb[i] = (kb[lc] * kr + kb[rc]) % MOD
            i >>= 1

    ans = [0] * nq
    for i in range(1, n + 1):
        for j in act[i]:
            k, b = ops[j]
            assign(j, k, b)
        for j in dea[i]:
            assign(j, 1, 0)                  # 写回恒等
        for T, oi in qs[i]:
            # 时间前缀 [0, T) 的复合：左段顺序累积，右段逆序累积，最后拼起来
            l = size; r = T + size
            kl = 1; bl = 0                   # 左半部分（靠前的时间）
            kr = 1; br = 0                   # 右半部分（靠后的时间）
            while l < r:
                if l & 1:
                    bl = (bl * km[l] + kb[l]) % MOD
                    kl = kl * km[l] % MOD
                    l += 1
                if r & 1:
                    r -= 1
                    br = (kb[r] * kr + br) % MOD
                    kr = km[r] * kr % MOD
                l >>= 1; r >>= 1
            ans[oi] = (a[i] * (kl * kr) + (bl * kr + br)) % MOD
    sys.stdout.write("\n".join(map(str, ans)) + "\n")


main()

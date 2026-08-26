"""BISHI79 取数游戏 —— N*M 矩阵取若干数，任意两数不能八连通相邻，求最大和。

这题考什么：
    表面上是「搜索 + 剪枝」，本质是**状压 DP（轮廓线 / 逐行压缩）**。
    关键观察：八连通相邻只会发生在「同一行相邻列」和「相邻两行且列号差 <= 1」，
    隔一行以上的两个格子永远不相邻。于是只要把「本行选了哪些列」压成一个
    M 位的二进制 mask，行与行之间的约束就只依赖前一行的 mask，可以逐行递推。

    合法性判定：
      - 行内：mask & (mask << 1) == 0（同行不能选相邻列）；
      - 行间：把上一行 mask1 向左右各扩一位得到 mask1 | mask1<<1 | mask1>>1，
        它与本行 mask2 无交集即可（一次与运算同时覆盖了正上方和两个斜上方）。

数据规模与复杂度：
    T <= 20，N, M <= 6。M = 6 时子集只有 64 个，行内合法的只有 21 个
    （斐波那契数 F(8)）。复杂度 O(T * N * 21 * 21) < 6e4，瞬间出结果。
    朴素 DFS 逐格枚举是 2^36 级别，必须靠这个压缩把指数降到「按行」。

坑在哪：
  1. mask >> 1 在 Python 里对非负整数是安全的（不会像某些语言那样出现符号位问题），
     但 mask << 1 可能超出 M 位，与 mask2 相与时高位自然是 0，无害；
  2. 多组数据，每组都要重置 dp，别把上一组的结果带进来；
  3. a_ij >= 1 全是正数，所以「一个都不选」只在被逼无奈时才最优；dp 初值取 0
     （即空行）是正确的，因为空 mask = 0 恒合法；
  4. 题面写「非负整数」但约束又写 1 <= a_ij，按非负处理即可，逻辑不受影响。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    # 每组的 n、m 都不一样，行数不固定，所以全程用一个 token 游标 p 顺序推进，
    # 不按行解析
    p = 0
    t = int(data[p]); p += 1
    out = []
    for _ in range(t):
        n, m = int(data[p]), int(data[p + 1]); p += 2
        rows = []
        for _ in range(n):                       # 逐行取 m 个数，游标随之推进
            rows.append([int(v) for v in data[p:p + m]])
            p += m

        full = 1 << m                            # mask 的取值范围是 [0, 2^m)
        # 行内合法的 mask（同行不选相邻列）
        masks = [s for s in range(full) if not (s & (s << 1))]
        # 每个 mask 向左右扩一位，用于判定与下一行是否冲突（正上 + 两斜上）
        spread = [s | (s << 1) | (s >> 1) for s in range(full)]

        # 逐行推进的状态压缩 DP：八连通只跨越相邻两行，所以「上一行选了什么」
        # 就是全部需要记住的历史，dp 只保留一行
        dp = [0] * full          # dp[mask]：上一行选 mask 时的最大和
        alive = [0]              # 上一行取值为 0（空行）作为哨兵起点
        for r in range(n):
            row = rows[r]
            # 本行每个合法 mask 的权值和。每组的 a 都不同，只能逐行重算；
            # 至多 21 个 mask，代价可以忽略
            val = {}
            for s in masks:      # 预处理本行每个 mask 的权值和
                tot = 0
                x = s
                while x:
                    low = x & -x                  # lowbit：取出最低位的那个 1
                    tot += row[low.bit_length() - 1]   # 位权 2^j 的 bit_length 是 j+1，故减 1 得列号
                    x ^= low                      # 清掉这一位，继续找下一个
                val[s] = tot
            # 转移：本行取 s2，在上一行的可达状态里挑一个不冲突且 dp 最大的
            ndp = [-1] * full                     # -1 表示该 mask 这一行还不可达
            for s2 in masks:
                best = -1                         # 上一行能接上 s2 的最大和
                for s1 in alive:
                    if spread[s1] & s2:
                        continue          # 与上一行八连通冲突
                    if dp[s1] > best:
                        best = dp[s1]
                if best >= 0:                     # 存在合法的上一行才有转移
                    ndp[s2] = best + val[s2]
            dp = ndp
            alive = [s for s in masks if dp[s] >= 0]   # 下一行只需在可达状态里挑
        out.append(str(max(dp)))                  # 最后一行的所有合法状态取最大
    sys.stdout.write("\n".join(out) + "\n")


main()

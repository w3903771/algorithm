"""BISHI135 三角形取数(Hard Version) —— 数字三角形，限制 |左下次数 - 右下次数| <= k。

这题考什么：
    先做一步**观察化简**，把看似二维的约束降成一维。

    三角形是**居中**摆放的（第 i 行有 2i-1 个数，两边各外扩一格）。
    给每个数一个「绝对列号」c：第 i 行的第 j 个数（j = 1..2i-1）的绝对列号是
        c = j + (n - i)
    这样一来：正下方 = c 不变，左下 = c-1，右下 = c+1，起点在 c = n。

    于是终点列号 c_end 满足
        c_end = n + (r - l)   =>   l - r = n - c_end
    **约束 |l - r| <= k 等价于「终点列号落在 [n-k, n+k] 内」**——
    根本不需要把 (l - r) 当成 DP 的一维状态！这是本题最大的坑/最大的收获。

    剩下就是最朴素的数字三角形 DP：
        f[i][j] = a[i][j] + max(f[i-1][j-2], f[i-1][j-1], f[i-1][j])
    （下标是「行内序号」，上一行序号比本行小 0/1/2，正好对应右下/正下/左下三种来法。）

数据规模与复杂度：
    n <= 300，总共 n^2 = 9e4 个数，DP 是 O(n^2)。
    若真把 (l-r) 当第三维会变成 O(n^3) = 2.7e7，虽然也能过但完全没必要。

坑在哪：
  1. **行内序号与绝对列号的换算**是本题的全部难点，画个 n=3 的图对一遍再动手；
  2. 边界：上一行的序号必须落在 [1, 2i-3] 内，越界的候选要跳过；
  3. a_{i,j} 可以是 -2e9，累加到 300 行会到 -6e11，C++ 必须 long long；
  4. 答案只在**最后一行**的合法列号范围内取最大值，不是全局最大。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); k = int(data[1])
    p = 2
    NEG = -(1 << 62)
    prev = [int(data[p])]                    # 第 1 行只有一个数
    p += 1
    for i in range(2, n + 1):
        w = 2 * i - 1
        row = data[p:p + w]
        p += w
        pw = len(prev)                       # = 2i-3
        cur = [0] * w
        for j in range(w):
            # 上一行的候选序号：j, j-1, j-2（0-indexed 下即 j-2..j）
            best = NEG
            lo = j - 2
            if lo < 0:
                lo = 0
            hi = j if j < pw else pw - 1
            for t in range(lo, hi + 1):
                v = prev[t]
                if v > best:
                    best = v
            cur[j] = int(row[j]) + best
        prev = cur
    # 最后一行的行内序号 j（1-indexed）就等于绝对列号，约束 |j - n| <= k
    lo = n - k
    if lo < 1:
        lo = 1
    hi = n + k
    if hi > 2 * n - 1:
        hi = 2 * n - 1
    sys.stdout.write("%d\n" % max(prev[lo - 1:hi]))


main()

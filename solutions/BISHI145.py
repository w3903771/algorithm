"""BISHI145 石子合并 —— 相邻两堆合并、代价为两堆之和，求最小总代价。

这题考什么：
    **区间 DP** 的模板题。
        f[l][r] = 把 [l, r] 合成一堆的最小代价
        f[l][r] = min_{l <= k < r} ( f[l][k] + f[k+1][r] ) + (m_l + ... + m_r)
    最后那一项与断点 k 无关（无论怎么合，最后一次合并的代价一定是整段之和），
    用前缀和 O(1) 取出。枚举顺序必须**按区间长度从小到大**，
    保证 f[l][k]、f[k+1][r] 都已算好。

    注意这题是**链**不是环（不需要破环成链复制一倍）。

数据规模与复杂度：
    N <= 300，状态 O(N^2) = 9e4，每个状态枚举 O(N) 个断点 → O(N^3) ≈ 4.5e6。

Python 关键：
    最内层的「枚举断点取 min」可以整段下沉到 C 层，但需要同时维护**转置表**：
        f[l][k]     -> f 的第 l 行，切片 f[l][l:r]
        f[k+1][r]   -> 第 r **列**，为此额外维护 fT[r][k+1] = f[k+1][r]
        断点取 min  -> min(map(add, f[l][l:r], fT[r][l+1:r+1]))
    这样 4.5e6 次加法/比较全在 C 层，实测 0.2 秒；
    写成 Python 三重循环大约要 4 秒，在 2 秒限制下必挂。

    （另一条路是 **Knuth 四边形不等式优化** 把复杂度降到 O(N^2)，
      本题满足决策单调性；但在 Python 里「O(N^3) 全 C 层」比「O(N^2) 全 Python 层」更快，
      这是 CPython 下非常典型的取舍。）

坑在哪：
  1. N = 1 时不需要任何合并，答案 0——不特判会输出错误的初值；
  2. f[i][i] = 0（单堆不需要合并），不是 m_i；
  3. 「代价」只累计合并操作，最终堆的质量不计入答案。
"""
import sys
from itertools import accumulate
from operator import add


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    a = list(map(int, data[1:1 + n]))
    if n == 1:
        sys.stdout.write("0\n")
        return
    pre = [0]
    pre.extend(accumulate(a))

    f = [[0] * n for _ in range(n)]          # f[l][r]
    fT = [[0] * n for _ in range(n)]         # fT[r][l] = f[l][r]，为了让内层能切列
    for length in range(2, n + 1):
        for l in range(0, n - length + 1):
            r = l + length - 1
            # min over 断点 k ∈ [l, r-1] of f[l][k] + f[k+1][r]
            v = min(map(add, f[l][l:r], fT[r][l + 1:r + 1])) + pre[r + 1] - pre[l]
            f[l][r] = v
            fT[r][l] = v
    sys.stdout.write("%d\n" % f[0][n - 1])


main()

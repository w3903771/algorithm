"""BISHI89 山峰数组计数 —— 把正整数数组切成三段，数有多少组切点 (i, j) 使 b1 < b2 > b3。

这题考什么：
    前缀和 + **单调性 + 二分计数**。设 S 为前缀和（S[0]=0），则
        b1 = S[i]，b2 = S[j] - S[i]，b3 = S[n] - S[j]。
    两个条件移项后都变成对 S[i] 的上界：
        b1 < b2      <=>  2*S[i] < S[j]
        b2 > b3      <=>  2*S[j] - S[i] > S[n]  <=>  S[i] < 2*S[j] - S[n]
    因为 P_i >= 1，S 是**严格递增**的，所以「S[i] < 某个阈值」的 i 恰好是
    一段前缀。固定 j，合法的 i 个数 = min(两个阈值各自的前缀长度, j-1)。
    用 bisect 在 S 上二分即可，总复杂度 O(n log n)。
    前缀和见 docs/part4-基础算法/42-前缀和与差分.md，二分见 docs/part4-基础算法/44-二分.md。

    （注意 2*S[i] < S[j] 这个条件本身就蕴含 i < j，所以它不需要额外截断；
      但第二个条件不蕴含，必须再和 j-1 取 min。）

数据规模与复杂度：
    n <= 2e5。暴力枚举 (i, j) 是 2e10 必 TLE；本做法 2e5 * 17 ≈ 3.4e6。
    （其实两个阈值都随 j 单调递增，可以做成双指针的 O(n)，
      但 bisect 是 C 实现，写起来更短且常数极小，这里用二分。）

坑在哪：
  1. 「2*S[i] < S[j]」化成「S[i] < (S[j]+1)//2」才是等价的整数形式：
     S[i] < S[j]/2 <=> S[i] <= ceil(S[j]/2) - 1 <=> S[i] < (S[j]+1)//2。
     直接写 S[j]//2 在 S[j] 为奇数时会少算一个；
  2. j 的范围是 2 <= j <= n-1（三段都非空，i >= 1 且 j < n）；
  3. 答案可达 C(2e5, 2) ≈ 2e10，C++ 要 long long；Python 无忧；
  4. bisect 要在「S[1..n]」这个严格递增列表上做，返回值直接就是满足条件的
     i 的个数（因为 i 从 1 开始编号）。

样例复核：
    P = [1,2,3,4,5]，S(1..5) = [1,3,6,10,15]。
    j=2: 阈值1 = (3+1)//2 = 2 -> 1 个；阈值2 = 6-15 = -9 -> 0 个；min = 0。
    j=3: 阈值1 = 3 -> 1 个；阈值2 = 12-15 = -3 -> 0 个；min = 0。
    j=4: 阈值1 = 5 -> 2 个；阈值2 = 20-15 = 5 -> 2 个；min(2,2,3) = 2。
    合计 2，与样例一致。
"""
import sys
from bisect import bisect_left
from itertools import accumulate


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    a = list(map(int, data[1:1 + n]))
    S = list(accumulate(a))              # S[k] = P_1 + ... + P_{k+1}，严格递增
    total = S[-1]                        # 整个数组的和，即 b1 + b2 + b3

    ans = 0
    for j in range(2, n):                # j 取 2..n-1（1-based），三段都非空
        sj = S[j - 1]                    # S 是 0-based 存的，S[j-1] 才是前 j 项之和
        # 条件一：2*S[i] < S[j]  <=>  S[i] < (S[j]+1)//2
        c1 = bisect_left(S, (sj + 1) // 2)
        # 条件二：S[i] < 2*S[j] - S[n]
        c2 = bisect_left(S, 2 * sj - total)
        c = c1 if c1 < c2 else c2        # 两个上界要同时满足，取更紧的那一个
        if c > j - 1:                    # i 必须严格小于 j
            c = j - 1
        if c > 0:                        # 阈值为负时 bisect 返回 0，此时没有合法的 i
            ans += c
    sys.stdout.write("%d\n" % ans)


main()

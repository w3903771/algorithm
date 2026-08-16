"""BISHI88 小苯的魔法染色 —— 至多 m 次区间覆盖，每次长度 <= k，把所有 'W' 盖住，求最小 k。

这题考什么：
    **二分答案 + 贪心判定**。k 越大越容易完成，可行性对 k 单调，于是二分 k。

    判定 check(k)：从左往右扫，遇到第一个还没被盖住的 'W'（设在位置 p），
    最优做法一定是把区间放成 [p, p+k-1]——起点再往左只会浪费长度，
    往右就盖不住 p。于是贪心地放一段、跳到 p+k 之后继续找下一个未覆盖的 'W'，
    统计用了几段，段数 <= m 即可行。这个贪心是「最少区间覆盖点集」的标准结论。

数据规模与复杂度：
    n <= 2e5。判定 O(n)（每次只在 W 位置列表上跳，用 bisect 更快，
    但线性扫已经够），二分 log n ≈ 18 次，总计约 3.6e6，稳过。
    这里把所有 W 的下标先收集成数组，判定时用 bisect 跳到下一个未覆盖的 W，
    单次判定降到 O(段数 * log n)，比逐格扫更快。

坑在哪：
  1. 若字符串本身全是 'R'（无 W），需要 0 次操作，任何 k 都行，
     而题目要求输出**正整数**，所以答案是 1（二分左端从 1 开始自然得到）；
  2. m <= n 保证了 k = n 一定可行（一次盖全），二分右端取 n 即可；
  3. 「至多 m 次」——用不满不扣分，判定写 <= m 而不是 == m；
  4. 输入的字符串单独一行且不含空格，用 split() 按 token 取正好是一整个串。

样例复核：
    n=5, m=2, s="WRWWR"，W 在下标 0,2,3。
    k=2: 盖 [0,1]，下一个未覆盖 W 是 2，盖 [2,3]，共 2 段 <= 2 ✓；
    k=1: 需要 3 段 > 2 ✗。答案 2，与样例一致。
"""
import sys
from bisect import bisect_left


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n, m = int(data[0]), int(data[1])
    s = data[2]
    W = ord('W')
    pos = [i for i in range(n) if s[i] == W]    # 所有待染格的下标
    if not pos:
        sys.stdout.write("1\n")                # 无需施法，最小正整数 k
        return

    total = len(pos)

    def ok(k: int) -> bool:
        used = 0
        i = 0
        while i < total:
            used += 1
            if used > m:
                return False
            # 本段覆盖 [pos[i], pos[i]+k-1]，跳到第一个不在该区间的 W
            i = bisect_left(pos, pos[i] + k, i + 1)
        return True

    lo, hi = 1, n                              # k=n 必可行（m>=1，一段盖全）
    while lo < hi:
        mid = (lo + hi) // 2
        if ok(mid):
            hi = mid
        else:
            lo = mid + 1
    sys.stdout.write("%d\n" % lo)


main()

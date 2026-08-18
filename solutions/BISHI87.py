"""BISHI87 [CQOI2010] 扑克牌 —— n 种牌各 c_i 张 + m 张 Joker，Joker 可顶替任意一种，
求最多能凑出多少套（一套 = n 种牌各一张，其中至多一张可用 Joker 顶替）。

这题考什么：
    **二分答案 + O(n) 判定**。直接贪心构造很容易漏情况，但「能否凑出 k 套」
    这个判定是单调的（k 可行 => k-1 可行），于是二分 k。
    二分答案的通用套路见 docs/part4-基础算法/44-二分.md。

    判定 check(k)：
      - 每套里同一种牌只用一张，所以第 i 种牌最多贡献 min(c_i, k) 张；
      - 缺口 need = Σ max(0, k - c_i)，这些位置只能拿 Joker 来补；
      - 两个限制同时成立才可行：
          need <= m   （Joker 总量够）
          need <= k   （每套至多用一张 Joker，k 套最多用 k 张）
        即 need <= min(m, k)。
    第二个限制是本题最容易漏的一条——只判 need <= m 会在
    「Joker 很多但某一种牌极少」时给出偏大的答案。

数据规模与复杂度：
    n <= 50，c_i、m <= 5e8。答案上界 (Σc_i + m) // n <= (50*5e8 + 5e8)/2 ≈ 1.3e10，
    二分约 35 次，每次 O(n = 50)，总共 ~1750 次运算，瞬间出结果。

坑在哪：
  1. 二分上界要够大：用 (sum(c) + m) // n + 1 作为「一定不可行」的右端；
  2. c_i 可以为 0（这一种牌完全没有），此时每套都得靠 Joker 顶它，
     need >= k 会立刻把答案压到 0 或很小，公式本身已经处理好；
  3. 答案可能是 0（比如两种牌其中一种为 0 且 m = 0），二分左端从 0 开始；
  4. C++ 里 need 累加会爆 int（50 * 1.3e10），要 long long；Python 无此问题。

样例复核：
    n=3, m=4, c=[1,2,3]。k=3: need = 2+1+0 = 3 <= min(4,3)=3 ✓；
    k=4: need = 3+2+1 = 6 > min(4,4)=4 ✗。答案 3，与样例一致。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n, m = int(data[0]), int(data[1])
    c = [int(v) for v in data[2:2 + n]]

    def ok(k: int) -> bool:
        """能否凑出 k 套：缺口既要够 Joker 补，也不能超过「每套至多一张 Joker」。"""
        if k == 0:
            return True                  # 一套都不凑总是可行，作为二分左端的兜底
        need = 0
        cap = m if m < k else k          # 缺口上限 = min(Joker 总数, 套数)
        for v in c:
            if v < k:                    # 这一种牌不够 k 张，差的部分只能靠 Joker 顶
                need += k - v
                if need > cap:           # 提前退出，省掉无谓累加
                    return False
        return True

    # 二分「可行 / 不可行」的分界，循环不变量：lo 始终可行、hi 始终不可行
    lo, hi = 0, (sum(c) + m) // n + 1    # hi 一定不可行
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if ok(mid):
            lo = mid                     # mid 可行，答案至少是 mid
        else:
            hi = mid                     # mid 不可行，答案严格小于 mid
    sys.stdout.write("%d\n" % lo)        # 退出时 hi = lo + 1，lo 就是最大可行套数


main()

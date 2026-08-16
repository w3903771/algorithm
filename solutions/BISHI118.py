"""BISHI118 相差不超过k的最多数 —— 选一个子集使 max-min <= k，求最大元素个数。

这题考什么：
    「集合中任意两数之差 <= k」只和 max、min 有关，与选取顺序无关，
    所以**排序后答案一定是一段连续区间**（排序后的下标区间）。
    问题化为：排序后找最长的区间 [l, r] 满足 a[r] - a[l] <= k。

    排序后 a 单调不减 => 固定 r 时，合法的最小 l 随 r 单调不减 => 双指针 O(n)。

数据规模与复杂度：
    n <= 2e5。排序 O(n log n)（Timsort，C 层），双指针 O(n)。
    朴素枚举两端是 O(n^2) = 4e10，必挂。

坑在哪：
  1. **必须先排序**——不排序直接对原数组做滑动窗口是错的，
     因为题目选的是子集不是子段；
  2. 相等元素要能全部选进来（用 <= 判断，不是 <）；
  3. 「可以一个都不选」是干扰项：n >= 1 时单个元素总是合法，答案至少是 1；
  4. a_i、k 都到 1e9，C++ 里做差不会溢出但要小心，Python 无此问题。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); k = int(data[1])
    a = sorted(map(int, data[2:2 + n]))
    l = 0
    best = 0
    for r in range(n):
        x = a[r]
        while x - a[l] > k:                  # 左端右移到合法为止（总共只走 n 步）
            l += 1
        if r - l + 1 > best:
            best = r - l + 1
    sys.stdout.write("%d\n" % best)


main()

"""BISHI85 【模板】整数域二分 —— 静态数组，q 次询问区间 [l, r] 内的元素个数。

这题考什么：
    整数域二分（lower_bound / upper_bound）的最标准模板：
        cnt([l, r]) = (第一个 > r 的位置) - (第一个 >= l 的位置)
                    = bisect_right(a, r) - bisect_left(a, l)
    先把数组排好序，此后每次询问都是 O(log n)。
    两个边界写法（第一个 >= x、第一个 > x）见 docs/basic/binary-search.md。

数据规模与复杂度：
    n, q <= 2e5。排序 O(n log n)，询问 O(q log n)，总计约 2e5 * 18 * 2 ≈ 7e6。
    暴力每次扫一遍是 4e10，必然 TLE。

Python 的坑：
  1. 手写二分（Python 层的 while 循环）大约要 2e5 * 18 = 360 万次迭代，
     而 bisect 模块是 C 实现，快一个数量级，**直接用 bisect 就是最优解**；
  2. 输入 4e5+ 个整数，必须 sys.stdin.buffer.read().split() 一次读完；
     逐行 input() 会慢十几倍；
  3. 输出 q 行，"\\n".join 一次性写出；
  4. 题面没有保证 l <= r。若真出现 l > r，两个 bisect 相减会是负数，
     所以外面套一个 max(0, ...) 兜底。
"""
import sys
from bisect import bisect_left, bisect_right


def main() -> None:
    data = sys.stdin.buffer.read().split()      # 4e5+ 个 token，一次性读完
    n, q = int(data[0]), int(data[1])
    a = sorted(map(int, data[2:2 + n]))         # 排序一次，此后数组只读不改

    out = []
    p = 2 + n                                   # 游标：数组之后紧跟着 q 组询问
    for _ in range(q):
        l = int(data[p]); r = int(data[p + 1]); p += 2
        # bisect_right(a, r) = 第一个 > r 的下标，bisect_left(a, l) = 第一个 >= l 的下标，
        # 两者相减恰好是落在 [l, r] 中的元素个数
        c = bisect_right(a, r) - bisect_left(a, l)
        out.append(str(c if c > 0 else 0))      # l > r 时差值为负，兜底成 0
    sys.stdout.write("\n".join(out) + "\n")     # q 行结果拼成一个串一次写出


main()

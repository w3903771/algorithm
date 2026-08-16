"""BISHI132 小红的地砖 —— 从第 1 块走到第 n 块，每步走 1 或 2 格，最小体力。

这题考什么：
    BISHI131 的「最优化」版本：把「方案计数」的加法换成「求最优」的 min。
        f_i = a_i + min(f_{i-1}, f_{i-2})
    含义：走到第 i 块必然是从 i-1 或 i-2 迈过来的，走到哪一块都要付出 a_i。

数据规模与复杂度：
    n <= 1e5，O(n) 时间、O(1) 空间（滚动两个变量即可，不用开数组）。

坑在哪：
  1. **n = 1 时答案是 0**（保证 a_1 = 0，且不需要移动），要特判，
     否则 f_2 的边界会越界；
  2. f_1 = a_1 = 0 是起点的体力（题目保证 a_1 = a_n = 0，但按 a_1 算更稳）；
  3. n = 2 时只能从 1 走到 2，min 里的 f_0 不存在——用「滚动变量初值」
     天然规避：令 prev2 = 无穷大即可，这里因为 f_1 = 0、n>=2 时直接从 f_2 起步。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    a = list(map(int, data[1:1 + n]))
    if n == 1:
        sys.stdout.write("0\n")
        return
    f2 = a[0]                                # f_1
    f1 = a[0] + a[1]                         # f_2：只能从第 1 块迈一步过来
    for i in range(2, n):
        f2, f1 = f1, a[i] + (f1 if f1 < f2 else f2)
    sys.stdout.write("%d\n" % f1)


main()

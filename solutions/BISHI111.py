"""BISHI111 【模板】差分 —— m 次区间加，最后一次性输出整个数组。

这题考什么：
    差分数组的裸模板。核心恒等式：
        令 d_i = a_i - a_{i-1}（d_1 = a_1），则「a[l..r] 全体加 k」
        等价于 d_l += k、d_{r+1} -= k 两次单点修改；
        最后对 d 做一次前缀和就还原出 a。
    「所有修改都在所有查询之前」是差分数组的适用信号——不需要树状数组。

数据规模与复杂度：
    n, m <= 1e5。朴素做法每次 for i in range(l, r+1) 是 O(nm) = 1e10，必然 TLE；
    差分是 O(n + m)，其中 m 次修改各 O(1)、最后一次 O(n) 前缀和。

坑在哪：
  1. d 要开到 n + 2 长度，因为 r 可以等于 n，会写 d[n+1]；
  2. k 可以是负数、a_i 也可以是负数，结果可能是负数，别用无符号思维；
  3. 输出是「一行 n 个整数」，必须 " ".join 一次性写出，
     用 n 次 print 会被 IO 拖死；
  4. 前缀和用 itertools.accumulate（C 层循环），比 Python for 快 5 倍以上。
"""
import sys
from itertools import accumulate


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    m = int(data[1])
    d = [0] * (n + 2)                       # 差分数组，多留一格给 r+1 = n+1
    p = 2 + n
    for _ in range(m):
        l = int(data[p]); r = int(data[p + 1]); k = int(data[p + 2])
        p += 3
        d[l] += k
        d[r + 1] -= k
    # accumulate(d[1:n+1]) 就是每个位置累计的增量，再和原数组逐项相加
    delta = accumulate(d[1:n + 1])
    a = map(int, data[2:2 + n])
    sys.stdout.write(" ".join(map(str, map(int.__add__, a, delta))) + "\n")


main()

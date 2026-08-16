"""BISHI41 【模板】整除分块 —— 求 Σ_{i=1..n} floor(n/i)，n <= 1e12。

这题考什么：
    直接循环 1e12 次显然不行。两条路都能到 O(sqrt n)：

    (1) 整除分块：floor(n/i) 只有 O(sqrt n) 种取值，对每个 i，
        使得 floor(n/j) == floor(n/i) 的最大 j 是 n // (n // i)，
        于是可以整块整块地跳。

    (2) 对称计数（本代码采用）：Σ_{i=1..n} floor(n/i) 其实是在数
        「满足 i*j <= n 的正整数对 (i,j) 的个数」。以 s = floor(sqrt n) 为界，
        把格点分成「i <= s」「j <= s」两块，二者重叠的是 s*s 的正方形，
        由容斥得
            答案 = 2 * Σ_{i=1..s} floor(n/i) - s^2。
        这是同样的 O(sqrt n)，但循环体只有一次整除，常数比整除分块还小，
        在 Python 里更划算（1e6 次迭代，约 0.1~0.2 秒）。

    验算 n = 10：s = 3，Σ = 10+5+3 = 18，2*18 - 9 = 27；
    手算 10+5+3+2+2+1+1+1+1+1 = 27 ✓。

数据规模与复杂度：
    n <= 1e12 -> sqrt(n) = 1e6，O(sqrt n) 时间、O(1) 空间。
    答案量级约 n·ln n ≈ 2.8e13，C/C++ 要 long long，Python 无忧。

坑在哪：
    1. sqrt 必须用整数开方 math.isqrt，浮点 int(n**0.5) 在 1e12 附近
       可能差 1，导致容斥的正方形边长算错；
    2. 容斥要减掉的是 s*s（重叠的正方形），不是 s；
    3. n = 1 时 s = 1，2*1 - 1 = 1 ✓，边界自然成立。
"""
import sys
from math import isqrt

n = int(sys.stdin.buffer.read().split()[0])
s = isqrt(n)
# 数格点 (i, j) 且 i*j <= n：两块各算一次，重叠的 s*s 减掉
print(2 * sum(n // i for i in range(1, s + 1)) - s * s)

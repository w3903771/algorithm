"""BISHI30 二进制数1 —— 求 x 的二进制表示里 1 的个数（popcount）。

这题考什么：
    最裸的 popcount。Python 里 bin(x) 直接给出 '0b...' 的二进制串，
    再 .count('1') 即可；'0b' 前缀里没有字符 '1'，所以不用切片也安全。

数据规模与复杂度：
    x <= 1e18 < 2^60，单组数据。bin() + count 都是 C 级实现，O(60) 位，
    常数极小。用 while x: x &= x-1 的 Brian Kernighan 循环同样 O(popcount)，
    但在 Python 里反而比 bin().count 慢。

坑在哪：
    1. x 可以是 0，此时 bin(0) = '0b0'，count('1') = 0，正好正确；
    2. 本项目要求兼容 Python 3.9，**不能用 int.bit_count()**（3.10 才有）；
    3. 1e18 超过 32 位，C/C++ 要开 unsigned long long，Python 无此问题。
"""
import sys

x = int(sys.stdin.buffer.read().split()[0])
print(bin(x).count("1"))

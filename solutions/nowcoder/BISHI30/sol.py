"""BISHI30 二进制数1 —— 求 x 的二进制表示里 1 的个数（popcount）。

这题考什么：
    最裸的 popcount（位计数，即二进制表示中 1 的个数）。
    Python 里 bin(x) 直接给出形如 '0b1101' 的二进制串，再 .count('1') 数一遍即可。
    前缀 '0b' 的两个字符里没有 '1'，所以不必先切片去前缀，直接数就是对的。

    换成手写循环（每次 x & 1 累加、x >>= 1）也能算，但那是 Python 层面的
    逐位迭代；bin() 与 str.count() 都在 C 层完成，实际更快也更短。
    位运算的系统讲解见 docs/basic/bit.md。

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

# 只有一个数，但仍走整块读入：split() 顺带去掉换行和多余空白
x = int(sys.stdin.buffer.read().split()[0])
# bin(x) 形如 '0b1000001'，前缀 '0b' 不含字符 '1'，直接计数即得 popcount
print(bin(x).count("1"))

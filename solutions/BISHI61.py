"""BISHI61 小q的数列 —— f(x)=f(⌊x/2⌋)+f(x mod 2)，求 f(n) 及该值首次出现的下标。

这题考什么：
    识破递推的本质：**f(n) = n 的二进制中 1 的个数（popcount）**。
    归纳证明：f(0)=0、f(1)=1 成立；x >= 2 时 x mod 2 就是最低位，
    ⌊x/2⌋ 是去掉最低位后的数，f(x) = popcount(x>>1) + 最低位 = popcount(x)。

    第二问：值 k 第一次出现在哪一项？就是「popcount 等于 k 的最小非负整数」，
    显然是把 k 个 1 全塞到最低位，即 2^k - 1。
    （k = 0 时是 0，公式同样给 0。）

数据规模与复杂度：
    T <= 5e5，n <= 1e18。每组 O(log n)（bin() 的开销），总量 5e5 * 60 位。
    真去按递推打表是不可能的（n 到 1e18）。
    Python 3.9 **没有 int.bit_count()**（那是 3.10 才加的），
    所以用 bin(x).count("1")；答案的第二部分 2^k-1 只有 61 种，预先打表成字符串。

坑在哪：
  1. 输入范围写的是 n >= 1，但官方样例里出现了 n = 0，必须能处理（答案 "0 0"）；
  2. T 高达 5e5，一定要 sys.stdin.buffer.read() 整块读 + "\n".join 一次输出，
     逐行 input()/print() 会被 IO 拖死；
  3. n 到 1e18 超过 int64，C++ 要 unsigned long long / __int128 小心，Python 无忧。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    first = [str((1 << k) - 1) for k in range(64)]   # popcount = k 时的最小下标
    out = []
    ap = out.append
    for tok in data[1:t + 1]:
        c = bin(int(tok)).count("1")                 # 3.9 无 int.bit_count()
        ap(str(c) + " " + first[c])
    sys.stdout.write("\n".join(out) + "\n")


main()

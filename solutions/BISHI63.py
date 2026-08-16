"""BISHI63 计算阶乘 —— T 组询问，每组求 n! mod (1e9+7)。

这题考什么：
    「多组询问 + 同一个上界」的经典套路：**预处理阶乘前缀表，O(1) 回答**。

数据规模与复杂度：
    T <= 1e3，n <= 1e6。
      - 每组都从头乘一遍是 O(T * n) = 1e9 次乘法取模，Python 下必死；
      - 预处理一次 fact[0..maxn] 是 O(maxn) = 1e6，之后每次询问 O(1)，
        总复杂度 O(maxn + T)。
    进一步的小优化：先把所有询问读进来取 max，只预处理到实际最大的 n，
    样例里 n = 1 时连表都不用建。

坑在哪：
  1. 一定要先读完全部输入再决定表的长度，所以用整块读取 + 游标；
  2. 递推 fact[i] = fact[i-1] * i % MOD，每步取模；
     若先算精确的 1e6! 再取模，那个数有 550 多万位，必然 TLE + MLE；
  3. 输出攒进列表最后 "\n".join 一次写出。
"""
import sys

MOD = 1000000007


def main() -> None:
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    ns = [int(x) for x in data[1:t + 1]]
    m = max(ns) if ns else 0

    fact = [1] * (m + 1)                 # 前缀阶乘表，只建一次，随后 O(1) 查表
    for i in range(2, m + 1):
        fact[i] = fact[i - 1] * i % MOD

    sys.stdout.write("\n".join(str(fact[n]) for n in ns) + "\n")


main()

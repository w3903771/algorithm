"""BISHI55 判断质数 —— 给定 n <= 1e12，判断是否为质数，输出 Yes / No。

这题考什么：
    试除法判素数的模板。只需要试除到 sqrt(n)：若 n = p*q 且 p <= q，
    则必有 p <= sqrt(n)，所以 sqrt(n) 以内没有因子就一定是质数。

数据规模与复杂度：
    n <= 1e12 → sqrt(n) <= 1e6。
    朴素逐个试除是 1e6 次循环；这里用 2、3 先筛掉，再只试 6k±1
    （因为 >3 的质数模 6 必为 1 或 5），循环次数降到约 3.3e5，Python 下 ~0.1s。
    单组数据，不值得上 Miller-Rabin。

坑在哪：
  1. **求平方根必须用 math.isqrt**。n 到 1e12 时 int(n ** 0.5) 会因为
     double 只有 53 位尾数而偏差 ±1，把完全平方数（如 999966000289 = 999983^2）
     误判成质数。isqrt 是精确整数开方，不会有这个问题；
  2. n = 1 不是质数（题目里 n 下界就是 1，必须特判）；
  3. 2 和 3 是质数，别被 6k±1 的逻辑漏掉；
  4. 循环条件写 i*i <= n 或者预先算好 isqrt(n) 都行，后者只算一次更快。
"""
import math
import sys


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n < 4:                       # 2, 3
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    r = math.isqrt(n)               # 精确整数开方，绝不用 n ** 0.5
    i = 5
    while i <= r:                   # 只需试除 6k-1 与 6k+1
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


n = int(sys.stdin.buffer.read().split()[0])
sys.stdout.write("Yes\n" if is_prime(n) else "No\n")

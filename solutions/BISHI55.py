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
  4. 循环条件写 i*i <= n 或者预先算好 isqrt(n) 都行，后者只算一次更快
     （本题 n 在循环中不变，所以可以先算；BISHI56 那种边除边缩小 n 的场景
      就得写 d*d <= n 才能跟着收紧）；
  5. 输出是 "Yes" / "No"，首字母大写，别写成 YES / yes。

样例复核：
    n = 2 -> n < 4 分支直接 True -> Yes ✓；
    n = 3 -> 同上 -> Yes ✓；
    n = 4 -> 被 n % 2 == 0 拦下 -> No ✓。

    素性判定与筛法见 docs/part7-数学/80-数论基础.md，
    math.isqrt 等内置函数见 docs/part1-python基础/13-内置函数速查.md。
"""
import math
import sys


def is_prime(n: int) -> bool:
    if n < 2:                       # 1 和 0 都不是质数，题目 n 下界是 1
        return False
    if n < 4:                       # 2, 3
        return True
    if n % 2 == 0 or n % 3 == 0:    # 先筛掉 2、3 的倍数，下面的轮子才成立
        return False
    r = math.isqrt(n)               # 精确整数开方，绝不用 n ** 0.5
    # 排除 2、3 的倍数后，剩下的数模 6 只能余 1 或 5，
    # 于是从 5 起每轮跳 6，一次试除 6k-1（即 i）与 6k+1（即 i+2）
    i = 5
    while i <= r:                   # 只需试除 6k-1 与 6k+1
        if n % i == 0 or n % (i + 2) == 0:
            return False            # 找到因子，立刻结束，无须扫完
        i += 6
    return True


n = int(sys.stdin.buffer.read().split()[0])
sys.stdout.write("Yes\n" if is_prime(n) else "No\n")

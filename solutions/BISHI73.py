"""BISHI73 【模板】欧拉函数计算Ⅰ ‖ 朴素求值：试除法 —— T 组询问，每组给 x <= 1e9，求 φ(x)。

    φ(x)（欧拉函数）= 1..x 中与 x 互质的数的个数。

这题考什么：
    欧拉函数的积性公式 + 试除法分解：
        φ(x) = x * ∏_{p | x} (1 - 1/p)
    实现上写成「每找到一个质因子 p，就 res = res // p * (p-1)」，
    先除后乘保证整除、也避免中间量膨胀。

数据规模与复杂度：
    T <= 5e3，x <= 1e9 -> 试除上界 sqrt(x) = 31623。
      - 朴素「d 从 2 枚举到 sqrt(x)」是 5e3 * 3.2e4 = 1.6e8 次 Python 取模，太慢；
      - 先用**埃氏筛**把 31623 以内的 3401 个质数筛出来，只拿质数去试除，
        最坏 5e3 * 3401 ≈ 1.7e7 次，降到原来的 1/10；
        而且大多数 x 会被小质因子迅速削小，实际远低于最坏值。
    筛法用 bytearray + 切片步长赋值，内层循环下沉到 C 层，建表几乎不耗时。

坑在哪：
  1. φ(1) = 1（约定），公式里没有质因子，res 保持 1，天然正确；
  2. 试除完若剩余 x > 1，它是一个大于 sqrt 的质因子，必须再乘一次 (1 - 1/x)，
     漏了这步的话像 x = 999999937（质数）就会输出 999999937 而不是 999999936；
  3. 循环条件用 p * p <= x（x 随除法缩小，上界自动收紧），比预先算死 isqrt 更快；
  4. 每个质因子只贡献一次 (p-1)/p，重数不影响 —— 除干净后继续找下一个。
"""
import math
import sys


def build_primes(limit: int) -> list:
    """埃氏筛：bytearray + 切片赋值，内层循环走 C。"""
    sieve = bytearray([1]) * (limit + 1)
    sieve[0:2] = b"\x00\x00"              # 0 和 1 不是质数
    for i in range(2, math.isqrt(limit) + 1):
        if sieve[i]:
            # 从 i*i 起划掉 i 的倍数：更小的倍数早被更小的质因子划过了。
            # 切片步长赋值把整个内层循环交给 C，比 for 逐个置 0 快得多
            sieve[i * i::i] = bytearray(len(range(i * i, limit + 1, i)))
    return [i for i in range(2, limit + 1) if sieve[i]]


def main() -> None:
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    primes = build_primes(31623)          # sqrt(1e9) 上取整，试除只需到这里
    out = []
    ap = out.append
    for tok in data[1:t + 1]:
        x = int(tok)
        res = x                           # 从 x 出发，每遇到一个质因子就乘上 (1 - 1/p)
        for p in primes:
            if p * p > x:                 # x 会随着除法缩小，上界随之收紧
                break
            if x % p == 0:
                res = res // p * (p - 1)  # 先除后乘，保证整除
                while x % p == 0:
                    x //= p               # 把 p 除干净：重数不影响 φ，每个质因子只算一次
        if x > 1:                         # 剩下的大质因子
            res = res // x * (x - 1)
        ap(str(res))
    sys.stdout.write("\n".join(out) + "\n")


main()

"""BISHI74 【模板】非质模数下的乘法逆元 —— T 组询问，求 a^(-1) mod m，m **不保证是质数**。

这题考什么：
    模数非质时费马小定理彻底失效（a^(m-2) 不再是逆元），必须用**扩展欧几里得**：
    解 a*x + m*y = gcd(a, m)。当 gcd(a, m) = 1 时 x 就是逆元，取 x mod m 转正。
    逆元存在的充要条件正是 gcd(a, m) = 1 —— 否则 a*x ≡ 1 (mod m) 无解，
    因为左边恒是 gcd 的倍数。

    Python 的捷径：**pow(a, -1, m)**（3.8 引入，3.9 当然支持）内部就是
    扩展欧几里得，逆元不存在时抛 ValueError。生产代码用它最省事；
    但这是「非质模数逆元」的模板题，下面把 exgcd 手写出来以展示原理，
    并在注释里给出 pow(a, -1, m) 的等价写法。

数据规模与复杂度：
    T <= 1e4，1 <= a < m <= 1e9。exgcd 是 O(log m)（约 45 层），
    手写迭代版（不用递归）避免函数调用与栈开销，总共 ~4.5e5 次循环，很快。

坑在哪：
  1. **m = 1 时**：模 1 意义下一切同余，逆元按惯例记作 0。
     但题目给的是 1 <= a < m，故 m >= 2，这种退化不会出现；
  2. **逆元不存在**（gcd(a,m) > 1）时题面没有规定输出什么——这是本题的题面歧义。
     输出描述只说「输出一行一个正整数」，从措辞看数据应当保证 gcd(a,m)=1；
     本题解在无解时输出 -1（竞赛最常见的约定），不影响有解数据的正确性；
  3. exgcd 出来的 x 可能是负数，必须 x % m 拉回 [0, m)；
  4. 别写成递归 exgcd —— T=1e4 时 Python 的递归开销明显，而且没必要。
"""
import sys


def inv(a: int, m: int) -> int:
    """扩展欧几里得求 a 在模 m 下的逆元；不存在返回 -1。迭代版，无递归开销。"""
    # 维护 old_r = old_s*a + (...)*m，对 (r, s) 做辗转相除
    old_r, r = a, m
    old_s, s = 1, 0
    while r:
        q = old_r // r
        old_r, r = r, old_r - q * r
        old_s, s = s, old_s - q * s
    if old_r != 1:            # gcd(a, m) != 1 -> 逆元不存在
        return -1
    return old_s % m          # 可能是负数，拉回 [0, m)


def main() -> None:
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    out = []
    for i in range(t):
        a = int(data[1 + 2 * i]); m = int(data[2 + 2 * i])
        # 等价一行写法（Python 3.8+）：
        #   try: v = pow(a, -1, m)
        #   except ValueError: v = -1
        out.append(str(inv(a, m)))
    sys.stdout.write("\n".join(out) + "\n")


main()

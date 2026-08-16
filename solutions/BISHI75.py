"""BISHI75 阶幂 —— fp(n) = n^fp(n-1)（fp(n)=1 当 n<=1），求 fp(n) mod (1e9+7)，n <= 1e6。

这题考什么：
    **欧拉降幂**（扩展欧拉定理）处理幂塔。
        a^b ≡ a^(b mod φ(m) + φ(m))  (mod m)   当 b >= φ(m)
        a^b ≡ a^b                    (mod m)   当 b <  φ(m)
    这条式子对 gcd(a,m) != 1 也成立，所以不需要讨论 n 与模数是否互质 —— 这正是
    「扩展」欧拉定理相对费马小定理的价值所在。

    于是递归：
        calc(n, m) = n^calc(n-1, φ(m)) mod m
    模数每递归一层就变成 φ(m)。关键事实：**φ 迭代最多 O(log m) 层就落到 1**
    （φ(m) <= m/2 对偶数成立；奇数 m 的 φ(m) 必为偶数，两步至少减半），
    m = 1e9+7 时约 60 层就到 1，到 1 后一切模 1 都是 0，可以直接返回。
    所以尽管 n 高达 1e6，递归深度只有 60 左右，与 n 无关。

数据规模与复杂度：
    n <= 1e6，但真正的递归层数 = min(n, φ 链长) ≈ 60。
    每层要算一次 φ（试除到 sqrt(m) <= 31623）和一次 pow(C 层快速幂)，
    总复杂度 O(log(P) * sqrt(P))，实测毫秒级。
    直接对 n 从 1 递推是不可能的：指数每层都要模不同的数。

    「b >= φ(m) 吗」的判定：不能真的去算 fp(n-1)（它是天文数字），
    但只要知道 fp 增长有多快就够了：
        fp(1)=1, fp(2)=2, fp(3)=9, fp(4)=4^9=262144, fp(5)=5^262144
    从 n >= 5 起 fp(n) 已经远超任何 m <= 1e9+7，所以只需硬编码前 4 项做比较。

坑在哪：
  1. 降幂条件必须是「指数 >= φ(m)」才加回 φ(m)；小于时**直接用原指数**，
     无脑 +φ(m) 会在 n 很小（如 n=2,3）时算错；
  2. m 递归到 1 时要立刻返回 0（模 1 恒为 0），否则 φ(1)=1 会死循环；
  3. 底数要先 n % m 再进 pow，n 可能远大于 m；
  4. n <= 1 时 fp(n) = 1，输出 1（样例 1）。
"""
import sys

MOD = 1000000007
# fp(1..4) 的精确值；n >= 5 时 fp(n) >= 5^262144，比任何模数都大得多
SMALL = (1, 1, 2, 9, 262144)


def phi(x: int) -> int:
    """试除法求欧拉函数。x <= 1e9+7，只需除到 sqrt(x)。"""
    res = x
    p = 2
    while p * p <= x:
        if x % p == 0:
            res = res // p * (p - 1)
            while x % p == 0:
                x //= p
        p += 1 if p == 2 else 2
    if x > 1:
        res = res // x * (x - 1)
    return res


def ge(n: int, m: int) -> bool:
    """判断 fp(n) >= m，不必真的算出 fp(n)。"""
    if n <= 4:
        return SMALL[max(n, 0)] >= m
    return True                     # fp(5) = 5^262144，碾压一切 m


def calc(n: int, m: int) -> int:
    """fp(n) mod m。"""
    if m == 1:
        return 0                    # 模 1 恒为 0，同时终止 φ 链
    if n <= 1:
        return 1                    # fp(0)=fp(1)=1，且此时 m >= 2
    pm = phi(m)
    e = calc(n - 1, pm)             # e = fp(n-1) mod φ(m)
    if ge(n - 1, pm):               # 指数 >= φ(m) 才做「+φ(m)」的降幂修正
        e += pm
    return pow(n % m, e, m)


n = int(sys.stdin.buffer.read().split()[0])
sys.stdout.write(str(calc(n, MOD)) + "\n")

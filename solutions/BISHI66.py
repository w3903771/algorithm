"""BISHI66 子数列求积 —— q 次询问区间乘积 mod (1e9+7)。

这题考什么：
    「前缀积 + 逆元」把区间乘积转成 O(1) 查询：
        ∏_{i=l..r} a_i = pre[r] * pre[l-1]^(-1)   (mod P)
    这正是前缀和的乘法版本；能这么做的前提是每个 a_i 在模 P 下可逆。

数据规模与复杂度：
    n, q <= 1e5，a_i < 1e9+7 = P 且 a_i >= 1，所以 a_i mod P != 0，
    前缀积恒不为 0，逆元必然存在（若题目允许 a_i 是 P 的倍数就得改用
    「记录 0 的个数 + 非零部分前缀积」的技巧）。

    逆元用**批量求逆**：只对 pre[n] 做一次 pow，然后倒推
        ipre[i-1] = ipre[i] * a_i mod P
    总共 O(n + q)，只有 1 次模幂。逐次 pow(pre[l-1], P-2, P) 也能过
    （1e5 次 C 层模幂 ~0.15s），但批量求逆是标准做法，也更能说明思路。

坑在哪：
  1. 询问是 1-indexed 的闭区间 [l, r]，对应 pre[r] * ipre[l-1]；
  2. 输出要求是**一行 q 个数用空格分隔**，不是每行一个；
  3. Python 3.8+ 也可以写 pow(x, -1, P) 直接求逆元（扩展欧几里得，
     3.9 支持），但这里只需要一次求逆，用 pow(x, P-2, P) 更贴模板；
  4. IO 量约 3e5 个整数，必须 buffer.read().split()。
"""
import sys

P = 1000000007


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); q = int(data[1])
    a = [int(x) % P for x in data[2:2 + n]]

    pre = [1] * (n + 1)
    for i in range(1, n + 1):
        pre[i] = pre[i - 1] * a[i - 1] % P

    ipre = [1] * (n + 1)                     # 批量求逆：只做一次模幂
    ipre[n] = pow(pre[n], P - 2, P)
    for i in range(n, 0, -1):
        ipre[i - 1] = ipre[i] * a[i - 1] % P

    out = []
    ap = out.append
    base = 2 + n
    for j in range(q):
        l = int(data[base + 2 * j]); r = int(data[base + 2 * j + 1])
        ap(str(pre[r] * ipre[l - 1] % P))
    sys.stdout.write(" ".join(out) + "\n")   # 一行输出，空格分隔


main()

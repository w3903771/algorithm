"""BISHI70 【模板】组合数 —— T 组询问，求 C(m, n) = m! / (n! (m-n)!) mod (1e9+7)。

这题考什么：
    质模数下的组合数模板：预处理阶乘 + 阶乘逆元，O(1) 回答单次询问。

    阶乘逆元的求法有两种：
      - 每个都 pow(fact[i], P-2, P)：O(maxn log P)，5e5 次模幂太浪费；
      - **倒推**：先算 inv_fact[maxn] = pow(fact[maxn], P-2, P)，再用
            inv_fact[i-1] = inv_fact[i] * i mod P
        （因为 1/(i-1)! = i / i!），一次模幂 + O(maxn) 乘法。这里用后者。

数据规模与复杂度：
    T <= 1e5，0 <= n <= m <= 5e5。
      - 每次现算 O(n) 的连乘是 O(T*m) = 5e10，必死；
      - 预处理 O(maxn) + 询问 O(1)，总 O(maxn + T)。
    表只开到输入中出现的最大 m，样例里就只有 5。

    P = 1e9+7 是质数且 P > maxn，所以 1..maxn 都与 P 互质，逆元全都存在，
    不需要 Lucas 定理（那是 m 超过模数时才要的）。

坑在哪：
  1. 题面写的是 C_m^n，即「从 m 个里选 n 个」，n 是下标、m 是上标，别读反：
     样例 "2 4" 给的是 n=2, m=4，答案 C(4,2)=6；
  2. 边界 n=0 或 n=m 时答案 1，阶乘表里 fact[0]=1 已经覆盖；
  3. 一定要先把全部询问读进来求 max，再决定表长（否则要无脑开到 5e5）；
  4. T 到 1e5，缓冲 IO 必需。
"""
import sys

P = 1000000007


def main() -> None:
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    ns = [int(x) for x in data[1:1 + 2 * t:2]]
    ms = [int(x) for x in data[2:2 + 2 * t:2]]
    mx = max(ms) if ms else 0

    fact = [1] * (mx + 1)
    for i in range(2, mx + 1):
        fact[i] = fact[i - 1] * i % P
    inv_fact = [1] * (mx + 1)
    inv_fact[mx] = pow(fact[mx], P - 2, P)      # 只做一次模幂
    for i in range(mx, 0, -1):                  # 1/(i-1)! = i * (1/i!)
        inv_fact[i - 1] = inv_fact[i] * i % P

    out = []
    ap = out.append
    for n, m in zip(ns, ms):
        ap(str(fact[m] * inv_fact[n] % P * inv_fact[m - n] % P))
    sys.stdout.write("\n".join(out) + "\n")


main()

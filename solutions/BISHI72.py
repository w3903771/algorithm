"""BISHI72 中位数之和 —— 01 数组的所有长度为 k（奇数）的子序列，中位数之和 mod (1e9+7)。

这题考什么：
    「0/1 值 => 求和 == 计数」+ 组合数。

    子序列元素只有 0 和 1，长度 k 为奇数，中位数 = 排序后第 (k+1)/2 个。
    中位数为 1  <=>  子序列里 1 的个数 >= (k+1)/2  （记 h = (k+1)//2）。
    因为中位数只能是 0 或 1，「中位数之和」= 「中位数为 1 的子序列个数」。

    设数组里共有 c1 个 1、c0 = n - c1 个 0，答案为
        ∑_{j=h}^{min(k, c1)}  C(c1, j) * C(c0, k - j)
    （从 1 里挑 j 个、从 0 里挑 k-j 个；j 也要满足 k-j <= c0）。
    注意：这里按**位置**计数，同值元素在不同下标算作不同子序列，正是题意。

    验算样例：n=5,k=1，全是 1 -> c1=5,c0=0,h=1，j=1：C(5,1)*C(0,0)=5 ✓

数据规模与复杂度：
    t <= 1e4，∑n <= 2e5，k <= n。
    预处理阶乘/阶乘逆元到 2e5（一次，全局），每组循环 O(k) <= O(n)，
    总复杂度 O(maxn + ∑n)。
    枚举「子序列本身」是 C(n,k) 级别的天文数字，只能用组合计数。

坑在哪：
  1. 逐组重建阶乘表会退化成 O(t * n)，必须在最外层建**一次**表；
     表长取所有测试用例里最大的 n 即可；
  2. 求和上界是 min(k, c1)，下界还要满足 k-j <= c0 即 j >= k-c0，
     统一用 C(x,y)=0 (y>x 或 y<0) 兜住最省心；
  3. 中位数是排序后第 (k+1)/2 个（1-indexed），k 为奇数时下标 h=(k+1)//2；
  4. 每组 n 可能很小但 t 很大，IO 必须整块读。
"""
import sys

P = 1000000007


def main() -> None:
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    idx = 1
    cases = []
    mx = 1
    for _ in range(t):
        n = int(data[idx]); k = int(data[idx + 1]); idx += 2
        c1 = 0
        for j in range(idx, idx + n):
            if data[j] == b"1":
                c1 += 1
        idx += n
        cases.append((n, k, c1))
        if n > mx:
            mx = n

    fact = [1] * (mx + 1)                     # 全局只建一次
    for i in range(2, mx + 1):
        fact[i] = fact[i - 1] * i % P
    inv_fact = [1] * (mx + 1)
    inv_fact[mx] = pow(fact[mx], P - 2, P)
    for i in range(mx, 0, -1):
        inv_fact[i - 1] = inv_fact[i] * i % P

    def C(a: int, b: int) -> int:
        if b < 0 or b > a:
            return 0
        return fact[a] * inv_fact[b] % P * inv_fact[a - b] % P

    out = []
    for n, k, c1 in cases:
        c0 = n - c1
        h = (k + 1) // 2                      # 至少要有 h 个 1，中位数才是 1
        s = 0
        for j in range(h, min(k, c1) + 1):
            s += C(c1, j) * C(c0, k - j) % P
        out.append(str(s % P))
    sys.stdout.write("\n".join(out) + "\n")


main()

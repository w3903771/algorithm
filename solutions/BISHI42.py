"""BISHI42 余数求和 —— 求 Σ_{i=1..n} (k mod i)，n,k <= 1e9。

这题考什么：
    把取模拆开：k mod i = k - i * floor(k/i)。于是
        答案 = n*k - Σ_{i=1..n} i * floor(k/i)。
    当 i > k 时 floor(k/i) = 0，这一项贡献为 0（对应 k mod i = k），
    所以后面那个和只需要算到 m = min(n, k)。

    Σ_{i=1..m} i * floor(k/i) 用**整除分块**：
    floor(k/i) 在一整段 i ∈ [l, r] 上取同一个值 v = k // l，
    其中 r = min(m, k // v)，这一段的贡献是 v * (l+r)*(r-l+1)/2。
    分块数是 O(sqrt k)。

    验算样例 n=10, k=5：n*k = 50；
    Σ i*floor(5/i) = 1*5 + 2*2 + 3*1 + 4*1 + 5*1 + 0... = 5+4+3+4+5 = 21；
    50 - 21 = 29 ✓（手算 0+1+2+1+0+5+5+5+5+5 = 29）。

数据规模与复杂度：
    n,k <= 1e9。逐项累加 k mod i 要循环 1e9 次，在任何语言里都超时；
    本解法的整除分块只有 O(sqrt k) ≈ 6.3e4 次迭代，毫秒级完成。
    答案量级最大约 n*k/2 ≈ 5e17，C/C++ 必须开 long long，Python 无上限。
    整除分块的推导与更多变形见 docs/part7-数学/83-整除分块与数论进阶.md。

坑在哪：
    1. n 可能大于 k，此时 i ∈ (k, n] 的每一项都等于 k，
       这部分被 n*k 与「Σ 只算到 min(n,k)」自动吸收，不要重复加；
    2. 分块右端点要对 m = min(n,k) 取 min，否则 i 会越界到 n 以外；
    3. 等差数列求和用整数除法 //2 而不是 /2（Python 3 的 / 是浮点，会丢精度）；
    4. k // l 在 l <= k 时恒 >= 1，所以 k // v 不会除零；循环从 l = 1 开始即可。
       注意 m = min(n, k) 保证了循环内一直有 l <= k，这一点是 v >= 1 的前提。
"""
import sys


def main() -> None:
    n, k = map(int, sys.stdin.buffer.read().split()[:2])
    m = min(n, k)                       # i > k 的项 floor(k/i) = 0，不必进循环
    total = 0
    l = 1
    while l <= m:
        v = k // l
        r = min(m, k // v)              # [l, r] 内 floor(k/i) 恒等于 v
        # 该段贡献 v * (l + l+1 + ... + r)，等差数列求和用整除避免浮点
        total += v * (l + r) * (r - l + 1) // 2
        l = r + 1                       # 跳到下一段的左端点
    print(n * k - total)


main()

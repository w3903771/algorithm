"""BISHI56 分解质因数 —— 把 n (2 <= n <= 1e12) 分解成从小到大的质因数列表。

这题考什么：
    试除法分解质因数的模板。从小到大枚举 d，只要 d | n 就一直除，
    除干净再继续。这样被除出来的 d 一定是质数：
    比 d 小的质因子在之前的轮次里已经被除光了。

数据规模与复杂度：
    n <= 1e12 → 只需试除到 sqrt(n) <= 1e6。
    同样用 2、3 + 6k±1 的轮子，循环约 3.3e5 次。
    循环结束后如果剩余的 n > 1，它就是最后一个（大于 sqrt 的）质因子，
    必须补输出 —— 这是本题最常见的漏点（例如 n 本身是质数，或 n = 2 * 大质数）。

坑在哪：
  1. 平方根用 math.isqrt；而且每除掉一次因子后 n 变小，上界要跟着更新
     （写成 d*d <= n 就自动跟随，最省事也最不易错）；
  2. 质因数重复出现要重复输出（18 -> "2 3 3"）；
  3. 行尾不能有多余空格，用 " ".join，不要循环 print(x, end=" ")；
  4. n 本身是质数时（比如 999999999989）循环内一个因子都找不到，
     全靠最后那句「剩余 > 1 就输出」。
"""
import sys


def main() -> None:
    n = int(sys.stdin.buffer.read().split()[0])
    res = []
    for d in (2, 3):
        while n % d == 0:
            res.append(d)
            n //= d
    d = 5
    while d * d <= n:               # d*d<=n 会随 n 缩小而自动收紧上界
        while n % d == 0:
            res.append(d)
            n //= d
        d += 2
        while n % d == 0:
            res.append(d)
            n //= d
        d += 4
    if n > 1:                       # 剩下的是大于 sqrt 的那个质因子
        res.append(n)
    sys.stdout.write(" ".join(map(str, res)) + "\n")


main()

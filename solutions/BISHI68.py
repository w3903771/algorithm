"""BISHI68 刷题统计 —— 已知并集 n、三个集合大小 a,b,c、恰好属于两个集合的人数 d，求三个都刷的人数。

这题考什么：
    容斥原理的「按重数计数」写法，不用背 |A∪B∪C| 的四项公式也能秒推。

    设 e1 / e2 / e3 分别是「恰好刷 1 / 2 / 3 个题单」的人数，则
        n     = e1 + e2 + e3            （并集：每人算一次）
        a+b+c = e1 + 2*e2 + 3*e3        （逐集合求和：恰好属于 k 个集合的人被数 k 次）
        d     = e2                      （题目直接给了）
    两式相减：a+b+c - n = e2 + 2*e3 = d + 2*e3，于是
        e3 = (a + b + c - n - d) / 2。

    验算样例：a+b+c = 16+16+22 = 54，n = 28，d = 12
              -> (54 - 28 - 12) / 2 = 14/2 = 7 ✓

数据规模与复杂度：
    T <= 1e3，每组 O(1)。

坑在哪：
  1. d 的定义是「**恰好**刷过其中任意两个题单的总人数」，不是
     |A∩B| + |B∩C| + |A∩C|（后者会把三个都刷的人重复计 3 次）。
     若按后一种定义则 a+b+c-n = d - 2*e3，符号完全相反，样例就对不上了；
  2. 除以 2 用整除 //（题目保证有唯一非负整数解，所以分子一定是偶数）；
  3. 数值到 3e9 超过 int32，C++ 要 long long。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    out = []
    for i in range(t):
        n = int(data[1 + 5 * i]); a = int(data[2 + 5 * i]); b = int(data[3 + 5 * i])
        c = int(data[4 + 5 * i]); d = int(data[5 + 5 * i])
        out.append(str((a + b + c - n - d) // 2))
    sys.stdout.write("\n".join(out) + "\n")


main()

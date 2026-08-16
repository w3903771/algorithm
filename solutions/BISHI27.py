"""BISHI27 构造数对 —— 找 (a,b) 满足 1<=a,b<=x、b|a、a*b>x、a/b<x。

这题考什么：
    看似构造，实则 x <= 100，直接 O(x^2) 暴力枚举全部数对即可（最多 1e4 次
    判断），根本不需要动脑推公式。数据规模决定做法的典型例子。

    顺带说一句规律：除了 x = 1 之外都有解。取 a = b = x 时
      - b | a 成立；
      - a*b = x^2 > x 当且仅当 x > 1；
      - a/b = 1 < x 当且仅当 x > 1。
    所以 x >= 2 时 (x, x) 恒为一组合法解，x = 1 时无解输出 -1。
    代码里仍然写暴力，既是对上面推论的自检，也避免推错。

数据规模与复杂度：
    x <= 100，O(x^2) = 1e4，瞬间出结果。

坑在哪：
    1. 条件 4 是严格小于：a/b < x，注意 a=b 时比值为 1，x=1 时 1<1 不成立；
    2. 条件 3 是严格大于 x，不是 >=；
    3. a/b 用整除判断即可（已保证 b|a），别写浮点比较；
    4. 答案不唯一，本地要用 special judge 校验。
"""
import sys


def main() -> None:
    x = int(sys.stdin.buffer.read().split()[0])
    for b in range(1, x + 1):
        for a in range(b, x + 1, b):        # 直接按 b 的倍数枚举 a，保证 b | a
            if a * b > x and a // b < x:
                print(a, b)
                return
    print(-1)


main()

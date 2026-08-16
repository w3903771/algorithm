"""BISHI53 [P1080] 国王游戏(简化版) —— 排大臣顺序，最小化「拿金币最多的人」。

这题考什么：
    相邻交换（exchange argument）推排序规则的经典模板题。
    设某两位相邻大臣为 i、j，他们前面所有人（含国王）的左手乘积为 S，
      - i 在前：两人分别拿 floor(S/b_i)、floor(S*a_i/b_j)
      - j 在前：两人分别拿 floor(S/b_j)、floor(S*a_j/b_i)
    去掉下取整比较（S 是公共因子，量级足够大时不改变大小关系），
    两种排法的最大值分别由 S*a_i/b_j 与 S*a_j/b_i 主导，
    即比较 a_i*b_i 与 a_j*b_j —— **按 a_i * b_i 升序排**，前面的人吃亏更小。

    排好之后从前往后累乘 a，逐个算 floor(前缀乘积 / b_i) 取最大值即可。

数据规模与复杂度：
    n <= 60，a_i,b_i <= 8。排序 O(n log n)，累乘 O(n)。
    真正的难点是 ∏a 最大到 8^60 ≈ 1.8e54，C++ 必须写高精度；
    Python 的 int 天生任意精度，这题因此变成纯模板。

坑在哪：
  1. 国王固定在最前，他自己不参与排序、也不领金币，但 a_0 要计入前缀乘积，
     b_0 完全没用（读掉丢弃即可）；
  2. 是「乘积除以 b_i 下取整」，必须用整除 //，用浮点会炸精度；
  3. 前缀乘积是「不含自己」的：先算 floor(prefix / b_i)，再把 a_i 乘进去。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    a0 = int(data[1])                 # data[2] 是 b0，用不到
    pairs = []
    for i in range(n):
        a = int(data[3 + 2 * i])
        b = int(data[4 + 2 * i])
        pairs.append((a * b, a, b))
    pairs.sort()                      # 按 a*b 升序

    prefix = a0                       # 当前大臣前面所有人的左手乘积
    ans = 0
    for _, a, b in pairs:
        v = prefix // b
        if v > ans:
            ans = v
        prefix *= a
    sys.stdout.write(str(ans) + "\n")


main()

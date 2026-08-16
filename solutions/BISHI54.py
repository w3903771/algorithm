"""BISHI54 货物堆放 —— 安排堆放顺序，最小化 ∑(v_i - c_i * 上方总重)。

这题考什么：
    又一道相邻交换求排序规则的贪心。
    ∑v_i 是常数，所以「最小化总体积」== 「最大化 ∑ c_i * W_i」（W_i = 上方总重）。

    看相邻两件 i、j，设它们上方总重为 P：
      - i 在上：c_i*P + c_j*(P + w_i)
      - j 在上：c_j*P + c_i*(P + w_j)
    作差得 c_j*w_i - c_i*w_j。要让它 > 0（i 放上面更优），即 c_j*w_i > c_i*w_j，
    也就是 **按 w_i / c_i 降序排**（压缩系数小、又重的货压在上面最划算）。

数据规模与复杂度：
    n <= 1e5。排序 O(n log n) + 一次前缀重量扫描 O(n)。

排序键：用精确整数键 (w << 128) // c，不用浮点 w/c，也不用 cmp_to_key
    两个不同比值 w1/c1 != w2/c2 的最小间隔是
        |w1*c2 - w2*c1| / (c1*c2) >= 1 / (c1*c2)。
    而键取 floor(w * 2^128 / c) 相当于把比值放大 2^128 再截断，
    量化步长 2^-128 ≈ 3e-39 远小于上面的最小间隔（c < 1e12 时也有 1e-24），
    所以不同比值一定映射到不同整数且严格保序 —— **精确**，且只是一次
    大整数移位 + 整除，n=1e5 实测 0.16s，比 functools.cmp_to_key 的
    O(n log n) 次 Python 层函数调用快得多。

    附：浮点键 w/c 其实也能被证明安全，但要靠一个不太直观的约束联动：
    c_i < v_i / ∑w <= 1e12 / ∑w 且 ∑w >= max w，故 w1*c2 < 1e12，
    误差项 2^-53 * (w1*c2 + w2*c1) < 2.2e-4 << 1，恰好压得住。
    既然整数键同样快，就没必要把正确性押在这条边界分析上。

坑在哪：
  1. c_i 可以是 0（题目允许 c_i >= 0），除零要单独处理：c=0 的货「怎么压都不缩」，
     比值视作 +∞，排最前面（放最上面）。用一个大于任何真实键的哨兵 1<<200 表示；
  2. 排序方向别搞反，是 w/c **降序**；
  3. v_i <= 1e12、n <= 1e5，总和可达 1e17，C++ 要 long long，Python 无所谓；
  4. 累加的是「上方的总重」，所以先用当前前缀重量算贡献，再把自己的 w 加进去。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    items = []
    total_v = 0
    INF = 1 << 200                    # 大于任何真实键的哨兵，给 c=0 用
    for i in range(n):
        w = int(data[1 + 3 * i])
        v = int(data[2 + 3 * i])
        c = int(data[3 + 3 * i])
        total_v += v
        items.append((-((w << 128) // c) if c else -INF, w, c))
    items.sort()                      # 键取负 -> 等价于 w/c 降序，c=0 排最前

    pref_w = 0                        # 已经放好的（在上方的）总重量
    save = 0
    for _, w, c in items:
        save += c * pref_w
        pref_w += w
    sys.stdout.write(str(total_v - save) + "\n")


main()

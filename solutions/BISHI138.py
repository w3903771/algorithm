"""BISHI138 【模板】多重背包 —— 第 i 种物品有 s_i 件，多组数据。

这题考什么：
    多重背包的 **二进制拆分**：把「最多取 s 件」拆成若干个 01 背包物品
        1, 2, 4, ..., 2^(t-1), s - (2^t - 1)
    这 t+1 个「打包物品」任意组合，恰好能凑出 0 ~ s 的**任意**件数
    （二进制表示 + 最后的余数补齐）。于是多重背包退化成 01 背包，
    复杂度 O(m · Σ log s_i)。

    两个必须做的预处理：
      1. **件数上限截断**：s <- min(s, m // w)。
         背包只有 m 的容量，取超过 m//w 件是不可能的。
         s_i 最大 1e6，不截断的话 log s ≈ 20；截断后大多数物品只剩 1-3 个拆分件；
      2. **体积为 0 的特判**（题目第 15、16 个测试点专门卡这个）：
         w = 0 的物品不占容量，直接把 s·v 全部计入答案，
         否则 `m // w` 会除零崩溃。

Python 关键：
    每个拆分件就是一次 01 背包的「整段取 max」：
        f[wt:] = list(map(max, f[wt:], [x + val for x in f[:m+1-wt]]))
    候选数组用赋值前的旧 f 计算，01 语义自动成立，且全程 C 层。

数据规模与复杂度：
    T <= 10，n, m <= 3000。截断后单组约 Σ(1 + log2(m/w_i)) ≈ 2.4n 个拆分件，
    每件 O(m) 的 C 层操作 → 单组约 2e7 次元素操作。

⚠️ Python 现实性：随机数据下 10 组约 2e8 次 C 层元素操作，**在 10 秒限制下偏险**；
    若数据构造成「w 全为 1、s 全为 1e6」（截断后每件 12 个拆分件），
    单组就是 1e8，几乎必然超时。题面也说了「时间限制较为宽松」，PyPy 下无压力。
    单调队列优化能做到 O(nm) 更优，但那是 9e6 次**纯 Python 层**迭代，
    在 CPython 里反而比这里的 C 层批处理更慢——**Python 的复杂度直觉和 C++ 不同**。

坑在哪：
  1. 二进制拆分的余项 `s - (2^t - 1)` 别漏，漏了就取不满 s 件；
  2. 拆分件的体积 wt = w·k 可能超过 m，要跳过（不跳过会切片错位）；
  3. w = 0 与 v = 0 的组合都要能正常跑（测试点 15/16）。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    p = 0
    T = int(data[p]); p += 1
    out = []
    for _ in range(T):
        n = int(data[p]); m = int(data[p + 1])
        p += 2
        f = [0] * (m + 1)
        base = 0                             # 体积为 0 的物品直接全拿
        for _ in range(n):
            w = int(data[p]); v = int(data[p + 1]); s = int(data[p + 2])
            p += 3
            if w == 0:
                base += s * v
                continue
            if v == 0 or w > m:
                continue
            if s > m // w:                   # 件数截断：拿再多也塞不下
                s = m // w
            k = 1
            while k <= s:
                wt = w * k; val = v * k
                f[wt:] = list(map(max, f[wt:], [x + val for x in f[:m + 1 - wt]]))
                s -= k
                k <<= 1
            if s > 0:                        # 余项，别漏
                wt = w * s; val = v * s
                f[wt:] = list(map(max, f[wt:], [x + val for x in f[:m + 1 - wt]]))
        out.append(f[m] + base)
    sys.stdout.write("\n".join(map(str, out)) + "\n")


main()

"""BISHI127 区间根号与区间求和 —— 区间开根 + 区间求和。

这题考什么：
    **势能分析 + 并查集跳跃**，是「单次最坏 O(n)、但总量有界」的经典模型。

    关键观察：开根收敛极快。
        1e7 -> 3162 -> 56 -> 7 -> 2 -> 1 -> 1 -> ...
    **任何数最多开 6 次根就落到 <= 1，之后再开根不变。**
    所以「区间开根」的**总**单点修改次数是 O(6n)，而不是 O(qn)。

    剩下的问题是「怎么跳过已经稳定（<= 1）的位置」——用**并查集**：
        nxt[i] = i 右边第一个还没稳定的位置。
    稳定一个就把它并到 i+1，之后所有查询自动跳过。

    区间和用**树状数组**（单点改 + 区间查，形态一），不需要线段树。

数据规模与复杂度：
    n, q <= 1e5，a_i <= 1e7。
    单点开根总次数 <= 6n = 6e5，每次一趟树状数组更新（<= 17 步）→ 1e7 次迭代；
    查询 1e5 * 2 * 17 = 3.4e6。合计约 1.4e7 次 Python 层循环。
    时限「其他语言 2 秒」——**非常险**，按 1e7 次/秒估算贴着上限。
    这是本题在 Python 下唯一有希望的写法（线段树版必挂）。

坑在哪：
  1. 必须用 **math.isqrt**，不能用 int(x ** 0.5)：
     后者在 1e7 附近可能因浮点误差差 1；
  2. 判「稳定」的条件是 **<= 1**（0 和 1 开根都是自己），不是 == 1；
  3. 2026-01-21 题面更新后 a_i >= 0，不必讨论负数开根；
  4. 并查集的 find 用**迭代 + 路径减半**，别写递归（深度可到 1e5）。
"""
import sys
from math import isqrt


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); q = int(data[1])
    a = [0] + [int(v) for v in data[2:2 + n]]

    t = [0] * (n + 1)                        # 树状数组，O(n) 建树
    for i in range(1, n + 1):
        t[i] += a[i]
        j = i + (i & -i)
        if j <= n:
            t[j] += t[i]

    nxt = list(range(n + 2))                 # 并查集：右边第一个 a > 1 的位置
    for i in range(1, n + 1):
        if a[i] <= 1:
            nxt[i] = i + 1

    def find(x):
        while nxt[x] != x:
            nxt[x] = nxt[nxt[x]]             # 路径减半
            x = nxt[x]
        return x

    p = 2 + n
    out = []
    push = out.append
    for _ in range(q):
        op = data[p]
        l = int(data[p + 1]); r = int(data[p + 2])
        p += 3
        if op == b"1":                       # 区间开根
            i = find(l)
            while i <= r:
                old = a[i]
                new = isqrt(old)
                a[i] = new
                d = new - old
                j = i
                while j <= n:                # 树状数组单点更新
                    t[j] += d
                    j += j & -j
                if new <= 1:                 # 稳定了，从并查集里摘掉
                    nxt[i] = i + 1
                i = find(i + 1)
        else:                                # 区间求和
            s = 0
            j = r
            while j > 0:
                s += t[j]; j -= j & -j
            j = l - 1
            while j > 0:
                s -= t[j]; j -= j & -j
            push(s)
    sys.stdout.write("\n".join(map(str, out)) + "\n")


main()

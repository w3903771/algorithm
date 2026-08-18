"""BISHI126 【模板】动态区间和Ⅱ —— 区间加 + 区间求和，n, q <= 5e5。

这题考什么：
    「区间修改 + 区间查询 + 求和」的标准解法有两个：懒标记线段树、**双树状数组**。
    题面自己都写了「也可以尝试区间扩展版的树状数组，其运行时的常数更小」——
    **在 Python 里这不是「也可以」，是「必须」。**

    树状数组（Fenwick tree，也叫二叉索引树 BIT）：下标 i 的格子负责一段长度为
    lowbit(i) = i & -i 的区间，求前缀和就沿 i -= lowbit(i) 逐段累加，
    单点加就沿 i += lowbit(i) 逐层上传，两条路径都只有 log n 步。
    见 docs/part3-数据结构/39-树状数组与线段树.md。

    双树状数组的推导：设 d 为差分数组（d_j = a_j - a_{j-1}），则
        Σ_{i<=k} a_i = Σ_{j<=k} (k - j + 1) d_j = k·Σ_{j<=k} d_j - Σ_{j<=k} (j-1)d_j
    所以维护两棵树：B1 存 d_j，B2 存 (j-1)·d_j。
      - 区间加 v 到 [l, r]：B1 上 l 处 +v、r+1 处 -v；
                            B2 上 l 处 +v(l-1)、r+1 处 -v·r；
      - 前缀和 pre(i) = i·B1.pre(i) - B2.pre(i)。

数据规模与复杂度：
    n, q <= 5e5，每次操作 O(log n)。
    Python 层循环迭代量：初始化 O(n)（用 O(n) 建树而不是 n 次 add）、
    每次修改 4 趟树、每次查询 2 趟双树，合计约 5e7 次。
    时限「其他语言 10 秒」，本文件这份写法在 Python 3 下实测通过；
    余量不宽裕，下面「卡常要点」里的四条都是必需的。

    对照：39.6 的非递归懒标记线段树每次操作约 6 log n = 114 次迭代，
    1e6 次操作就是 1.1e8 —— 在同样的时限下没有希望。
    这就是「能用树状数组就别写线段树」的实证。

Python 卡常要点（全部已用上）：
  1. 初始数组用 **O(n) 建树**：先把差分写进 t1/t2，再一趟把 t[i] 累加到 t[i+lowbit(i)]，
     比 n 次 range_add（1.9e7 次迭代）快一个 log；
  2. **两棵树放在同一个 while 循环里走**，循环次数减半；
  3. range_add / pre 写成闭包，全部走局部变量；
  4. 输出一次性 "\\n".join。

坑在哪：
    数组要开到 n+1（r+1 最大是 n+1），否则 add(r+1, ·) 越界或被静默丢弃。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); q = int(data[1])
    N = n + 1                                # 多留一格给 r+1
    t1 = [0] * (N + 1)                       # 维护 d_j
    t2 = [0] * (N + 1)                       # 维护 (j-1)·d_j

    # ---- O(n) 建树：差分 d_i 与加权差分 (i-1)d_i ----
    # 先把差分值原样放进 t1[i] / t2[i]，此时数组还只是「裸值」而非树状数组
    prev = 0                                 # a_0 视为 0，于是 d_1 = a_1
    for i in range(1, n + 1):
        v = int(data[1 + i])
        d = v - prev
        prev = v
        t1[i] = d
        t2[i] = (i - 1) * d
    # 再一趟把每个格子上传给它的父节点，就地变成树状数组。
    # i & -i 是 lowbit：只保留 i 最低位的 1，i + lowbit(i) 即 i 的父节点。
    # 这比调用 n 次单点 add 少一个 log 的迭代量。
    for i in range(1, N + 1):
        j = i + (i & -i)
        if j <= N:
            t1[j] += t1[i]
            t2[j] += t2[i]

    p = 2 + n
    out = []
    push = out.append
    for _ in range(q):
        if data[p] == b"1":                  # 区间加
            l = int(data[p + 1]); r = int(data[p + 2]); x = int(data[p + 3])
            p += 4
            # 差分视角：[l, r] 加 x 等价于 d_l += x、d_{r+1} -= x，
            # 两棵树同一趟循环里一起改，循环次数减半
            i = l; w = x * (l - 1)           # t2 上的配套增量是 (l-1)·x
            while i <= N:
                t1[i] += x; t2[i] += w
                i += i & -i                  # 沿 lowbit 向上，最多 log N 步
            i = r + 1; nx = -x; w = x * r    # 右端 r+1 处抵消，配套增量是 ((r+1)-1)·x = r·x
            while i <= N:
                t1[i] += nx; t2[i] -= w
                i += i & -i
        else:                                # 区间求和
            l = int(data[p + 1]); r = int(data[p + 2])
            p += 3
            # 前缀和公式：pre(i) = i·Σd_j - Σ(j-1)d_j，两棵树各查一次
            s1 = 0; s2 = 0; j = r
            while j > 0:
                s1 += t1[j]; s2 += t2[j]
                j -= j & -j                  # 沿 lowbit 向下，逐段拼出前缀
            res = s1 * r - s2                # pre(r)
            s1 = 0; s2 = 0; j = l - 1
            while j > 0:
                s1 += t1[j]; s2 += t2[j]
                j -= j & -j
            push(res - (s1 * (l - 1) - s2))  # 区间和 = pre(r) - pre(l-1)
    sys.stdout.write("\n".join(map(str, out)) + "\n")


main()

"""BISHI112 【模板】二维前缀和 —— q 次子矩阵求和查询。

这题考什么：
    二维前缀和的容斥公式。令
        P[i][j] = 左上角 (1,1) 到 (i,j) 的矩形和
    递推：P[i][j] = P[i-1][j] + P[i][j-1] - P[i-1][j-1] + a[i][j]
    查询：S(x1,y1,x2,y2) = P[x2][y2] - P[x1-1][y2] - P[x2][y1-1] + P[x1-1][y1-1]
    「减两次多减了左上角那块，要加回来」是容斥的全部内容。

数据规模与复杂度：
    n, m <= 1e3（矩阵最多 1e6 个数），q <= 1e5。
    预处理 O(nm)，每次查询 O(1)。若每次查询暴力累加，最坏 1e5 * 1e6 = 1e11，必挂。

Python 实现要点：
  1. 用**一维扁平数组**存 P，宽度 W = m+1，下标 i*W+j。
     二维嵌套 list 每次要走两级索引，1e5 次查询 * 4 次访问的差距不小；
  2. 每一行的构建拆成两步纯 C 层操作：
       行内前缀和 -> itertools.accumulate
       与上一行逐项相加 -> map(add, 上一行, 本行行内前缀和)
     这样 1e6 个格子的预处理不写一个 Python 层循环体；
  3. 读入 1e6 + 4e5 个 token，必须 sys.stdin.buffer.read().split()。

坑在哪：
    行/列下标从 1 开始，P 要多开一圈 0（第 0 行、第 0 列全 0），
    否则 x1-1 = 0 时会越界或取到错误的值。
"""
import sys
from itertools import accumulate
from operator import add


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); m = int(data[1]); q = int(data[2])
    W = m + 1
    pre = [0] * ((n + 1) * W)               # 多开第 0 行、第 0 列
    p = 3
    for i in range(1, n + 1):
        row = map(int, data[p:p + m])
        p += m
        cur = [0]                            # 行内前缀和，cur[0] = 0
        cur.extend(accumulate(row))
        base = i * W
        prev = base - W
        # P[i][j] = P[i-1][j] + (本行 1..j 的和)
        pre[base:base + W] = map(add, pre[prev:prev + W], cur)

    out = []
    push = out.append
    for _ in range(q):
        x1 = int(data[p]); y1 = int(data[p + 1])
        x2 = int(data[p + 2]); y2 = int(data[p + 3])
        p += 4
        b2 = x2 * W
        b1 = (x1 - 1) * W
        push(pre[b2 + y2] - pre[b1 + y2] - pre[b2 + y1 - 1] + pre[b1 + y1 - 1])
    sys.stdout.write("\n".join(map(str, out)) + "\n")


main()

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
  1. 行/列下标从 1 开始，P 要多开一圈 0（第 0 行、第 0 列全 0），
     否则 x1-1 = 0 时会越界或取到错误的值；
  2. 扁平化后行宽是 W = m+1（含第 0 列），(i, j) 的下标是 i*W + j。
     行宽写成 m 就会让相邻两行错位一格，症状是越靠下的行越离谱；
  3. a_{i,j} 可以为负，前缀和不单调，但容斥公式与单调性无关；
  4. 矩阵和最大 1e6 * 1e9 = 1e15，C++ 必须 long long；Python 无忧；
  5. 输出 1e5 行，用 "\\n".join 一次性写出，逐行 print 会被 IO 拖死。
"""
import sys
from itertools import accumulate
from operator import add


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); m = int(data[1]); q = int(data[2])
    W = m + 1                                # 扁平数组的行宽，(i, j) 落在 i*W + j
    pre = [0] * ((n + 1) * W)               # 多开第 0 行、第 0 列
    # ---- 逐行构建二维前缀和：每行只有一次 Python 层迭代 ----
    p = 3
    for i in range(1, n + 1):
        row = map(int, data[p:p + m])
        p += m
        cur = [0]                            # 行内前缀和，cur[0] = 0
        cur.extend(accumulate(row))
        base = i * W                         # 本行在扁平数组里的起点
        prev = base - W                      # 上一行的起点
        # P[i][j] = P[i-1][j] + (本行 1..j 的和)
        # 整行用一次 map(add, ...) 切片赋值搞定，全程留在 C 层
        pre[base:base + W] = map(add, pre[prev:prev + W], cur)

    # ---- 回答查询：每次四个点做容斥，O(1) ----
    out = []
    push = out.append
    for _ in range(q):
        x1 = int(data[p]); y1 = int(data[p + 1])
        x2 = int(data[p + 2]); y2 = int(data[p + 3])
        p += 4
        b2 = x2 * W                          # 下边界所在行的起点
        b1 = (x1 - 1) * W                    # 上边界再往上一行；x1 = 1 时正好落在全 0 的第 0 行
        # 大矩形 - 上方多余 - 左方多余 + 左上角（被减了两次，补回来）
        push(pre[b2 + y2] - pre[b1 + y2] - pre[b2 + y1 - 1] + pre[b1 + y1 - 1])
    sys.stdout.write("\n".join(map(str, out)) + "\n")


main()

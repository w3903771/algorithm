"""BISHI16 计算一年中的第几天 —— 多组数据读到 EOF。

考点：闰年判定 + 月份天数前缀和。每组 O(1)。

坑：
  1. **没有给组数**，题面只说「输入可能有多组测试数据」，必须一直读到 EOF；
     用 sys.stdin.buffer.read().split() 一把梭最省事，也不怕行尾空白/空行。
  2. 闰年：能被 4 整除且不能被 100 整除，或能被 400 整除；只有 3 月及以后才 +1。
"""
import sys

# 每月天数的前缀和（平年）：PRE[m] = 1..m-1 月的总天数
PRE = [0, 0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]

data = sys.stdin.buffer.read().split()
out = []
for i in range(0, len(data) - 2, 3):
    y, m, d = int(data[i]), int(data[i + 1]), int(data[i + 2])
    leap = (y % 4 == 0 and y % 100 != 0) or y % 400 == 0
    out.append(PRE[m] + d + (1 if leap and m > 2 else 0))
sys.stdout.write("\n".join(map(str, out)) + "\n")

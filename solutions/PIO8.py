"""PIO8 单组_二维数组 —— n 行 m 列求总和。

要点：二维数组求和不必真的建二维表；把剩下的 token 全部相加即可。
"""
import sys

data = sys.stdin.buffer.read().split()
n, m = int(data[0]), int(data[1])
print(sum(map(int, data[2:2 + n * m])))

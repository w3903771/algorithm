"""BISHI10 小红的字符串修改 —— 把 s 变成 t 的某个子串（连续区间）的最小改字母代价。

考点：枚举对齐位置 + 环形字母距离。
规模：|s|, |t| <= 1e3，对齐位置至多 1e3 个，每个位置比较至多 1e3 个字符，
      总量 1e6 次基本运算，Python 直接双重循环即可（用 map/sum 走 C 层更稳）。

坑：
  1. 'a' 和 'z' 是相邻的（字母表环形），代价是 min(|x-y|, 26-|x-y|)，
     不能简单用 abs(ord(x)-ord(y))。
  2. 这里的「子串」是连续子串（题面说的是从开头和结尾各删若干字符），
     不是子序列，所以只需枚举起点做定长对齐。
"""
import sys
from operator import add

data = sys.stdin.buffer.read().split()
s = data[0].decode()
t = data[1].decode()
n, m = len(s), len(t)

# 扁平化的 26*26 代价表：cost[i * 26 + j] = 字母 i 变到字母 j 的最少次数
cost = [min(abs(i - j), 26 - abs(i - j)) for i in range(26) for j in range(26)]

base = [(ord(c) - 97) * 26 for c in s]     # s 每一位在代价表中的行首偏移
tc = [ord(c) - 97 for c in t]              # t 每一位的字母编号

# 枚举 s 在 t 中的起始对齐位置；map(add, ...) 把「行首 + 列号」的下标计算放到 C 层
best = min(sum(map(cost.__getitem__, map(add, base, tc[off:off + n])))
           for off in range(m - n + 1))
print(best)

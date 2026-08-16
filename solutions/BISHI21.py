"""BISHI21 【模板】排序 —— 直接排序输出。

考点：n <= 1e5，用内置 sort（Timsort，O(n log n)）即可。
      这类题的真正瓶颈在 IO：逐行 input() / 逐个 print 会被卡，
      所以一次性读入 + 一次性输出。

小技巧：读进来的 token 先排成 int，输出时再转回字符串；
        也可以直接对 bytes 排序——但那是字典序，负数和位数不同的数会错，别偷这个懒。
"""
import sys

data = sys.stdin.buffer.read().split()
n = int(data[0])
a = sorted(map(int, data[1:n + 1]))
sys.stdout.write(" ".join(map(str, a)) + "\n")

"""PIO7 多组_一维数组_T组形式 —— t 组，每组先给 n 再给 n 个数。

要点：多组 + 大数据量，必须用「一次性读入 + 游标推进」。
"""
import sys

data = sys.stdin.buffer.read().split()
p = 0
t = int(data[p]); p += 1
out = []
for _ in range(t):
    n = int(data[p]); p += 1
    out.append(sum(map(int, data[p:p + n])))
    p += n
sys.stdout.write("\n".join(map(str, out)) + "\n")

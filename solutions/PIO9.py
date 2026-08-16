"""PIO9 多组_二维数组_T组形式。

要点：同 PIO7，只是每组要跳过 n*m 个 token。
"""
import sys

data = sys.stdin.buffer.read().split()
p = 0
t = int(data[p]); p += 1
out = []
for _ in range(t):
    n, m = int(data[p]), int(data[p + 1]); p += 2
    cnt = n * m
    out.append(sum(map(int, data[p:p + cnt])))
    p += cnt
sys.stdout.write("\n".join(map(str, out)) + "\n")

"""PIO5 多组_A+B_零尾模式 —— 以 0 0 作为输入结束标志。

要点：读到哨兵就 break，且哨兵本身不参与输出。
"""
import sys

data = sys.stdin.buffer.read().split()
out = []
i = 0
while i + 1 < len(data):
    a, b = int(data[i]), int(data[i + 1])
    i += 2
    if a == 0 and b == 0:
        break
    out.append(a + b)
sys.stdout.write("\n".join(map(str, out)) + "\n")

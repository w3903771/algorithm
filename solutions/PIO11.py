"""PIO11 多组_字符串_T组形式。

要点：字符串题同样怕逐行 input()。这里按 token 读，因为串内无空格。
"""
import sys

data = sys.stdin.buffer.read().split()
t = int(data[0])
out = []
p = 1
for _ in range(t):
    p += 1                                # 跳过 n
    out.append(data[p].decode()[::-1])
    p += 1
sys.stdout.write("\n".join(out) + "\n")

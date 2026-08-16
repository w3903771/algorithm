"""PIO4 多组_A+B_T组形式 —— 首行给出组数 t。

要点：t 可达 1e5，逐行 input() 会慢。一次性读入全部 token 再按下标推进，
是竞赛里最通用的高速读入范式。
"""
import sys

data = sys.stdin.buffer.read().split()
t = int(data[0])
out = []
for i in range(t):
    a = int(data[1 + 2 * i])
    b = int(data[2 + 2 * i])
    out.append(a + b)
sys.stdout.write("\n".join(map(str, out)) + "\n")

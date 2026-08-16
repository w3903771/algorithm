"""PIO12 单组_二维字符数组 —— 行和列都倒置。

要点：行列同时倒置 = 把每行反转后，再把行的顺序反转。
"""
import sys

data = sys.stdin.buffer.read().split()
n, m = int(data[0]), int(data[1])
rows = [data[2 + i].decode() for i in range(n)]
sys.stdout.write("\n".join(r[::-1] for r in reversed(rows)) + "\n")

"""PIO13 多组_带空格的字符串_T组形式 —— 去掉空格后倒置。

要点：串内含空格，就**不能**按 token 读，必须按行读。
      readline() 比 input() 快，且不会吞掉行尾信息。
"""
import sys

inp = sys.stdin
t = int(inp.readline())
out = []
for _ in range(t):
    inp.readline()                        # n
    s = inp.readline().rstrip("\n")
    out.append(s.replace(" ", "")[::-1])
sys.stdout.write("\n".join(out) + "\n")

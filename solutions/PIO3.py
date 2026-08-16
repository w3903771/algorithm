"""PIO3 多组_A+B_EOF形式 —— 读到文件末尾为止。

要点：Python 里 EOF 模式最稳的写法是直接 for line in sys.stdin，
不要用 while True: try: input() except EOFError —— 慢且啰嗦。
"""
import sys

out = []
for line in sys.stdin:
    if not line.split():          # 跳过空行
        continue
    a, b = map(int, line.split())
    out.append(a + b)
sys.stdout.write("\n".join(map(str, out)) + "\n")

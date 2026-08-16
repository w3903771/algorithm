"""BISHI18 多项式输出 —— 按规则把系数序列格式化成多项式字符串。

考点：纯字符串模拟，n <= 100，复杂度 O(n)。全部难度都在细节：

  1. 系数为 0 的项整项省略（包括常数项）。
  2. 次数 >= 1 且 |系数| == 1 时省略这个 1，只写 x / x^k；
     但**常数项**的 1 或 -1 必须完整输出（样例 2 的结尾 "+1"）。
  3. 次数 1 写 "x"（不是 "x^1"），次数 0 只写数字。
  4. 第一个被输出的项若为正数不带 '+'；它后面的正项都要带 '+'。
     注意「第一个输出的项」就是最高次项（题目保证 a_n != 0），
     但用「parts 是否为空」来判断更保险。
"""
import sys

data = sys.stdin.buffer.read().split()
n = int(data[0])
coef = list(map(int, data[1:n + 2]))      # 依次是 a_n, a_{n-1}, ..., a_0

parts = []
for idx, a in enumerate(coef):
    k = n - idx                            # 当前项的次数
    if a == 0:
        continue
    sign = "-" if a < 0 else ("+" if parts else "")
    v = abs(a)
    if k == 0:
        term = str(v)                      # 常数项：即使是 1 也要写出来
    else:
        head = "" if v == 1 else str(v)    # 次数 >= 1 时的系数 1 省略
        term = head + ("x" if k == 1 else "x^" + str(k))
    parts.append(sign + term)

sys.stdout.write("".join(parts) + "\n")

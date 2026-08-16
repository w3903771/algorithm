"""BISHI22 分数线划定 —— 按成绩降序（同分按报名号升序）排序后取第 t 名的分数当分数线。

考点：多关键字排序。n <= 5000，O(n log n) 绰绰有余。

流程：
  t = floor(1.5m) = 3m // 2（整数写法，避免浮点 1.5*m 的精度问题）；
  排序后第 t 名（1-based，即下标 t-1）的成绩就是分数线 line；
  所有成绩 >= line 的人全部进面试，人数可能超过 t（同分的都要进）。

坑：
  1. 分数线是「第 t 名的成绩」，不是「前 t 名」；同分者一律录取，所以 cnt >= t。
  2. 排序必须是 (-成绩, 报名号)，同分时报名号小的在前。
  3. 用 3*m//2 而不是 int(1.5*m)：m 是整数时两者结果相同，但整除写法永远安全。
  4. 约束只保证 m <= n，所以 m 接近 n 时 floor(1.5m) 可能**超过总人数**（如 n=m=5 时 t=7），
     必须 min(t, n) 夹一下，否则会下标越界。
"""
import sys

data = sys.stdin.buffer.read().split()
n, m = int(data[0]), int(data[1])
people = []
for i in range(n):
    k = int(data[2 + 2 * i])
    s = int(data[3 + 2 * i])
    people.append((-s, k))
people.sort()                       # 成绩降序、同分报名号升序

t = min(3 * m // 2, n)              # floor(1.5 * m)；m 接近 n 时 t 会超过总人数，需要夹住
line = -people[t - 1][0]

out = []
sel = [(k, -ns) for ns, k in people if -ns >= line]
out.append("%d %d" % (line, len(sel)))
for k, s in sel:
    out.append("%d %d" % (k, s))
sys.stdout.write("\n".join(out) + "\n")

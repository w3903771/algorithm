"""BISHI14 特殊的科学计数法 —— 把最多 1e5 位的大整数写成 a.b*10^c。

考点：大整数按**字符串**处理 + 严格四舍五入。
      N 有 1e5 位，绝不能 int(N) 之后做浮点运算（float 只有 15~16 位有效数字，
      直接把答案舍没了）。真正需要的信息只有三个：
        c = 位数 - 1（指数）
        前三位数字 —— 把 N 四舍五入到 2 位有效数字只用得到第 3 位来进位
      复杂度 O(|N|)（就是读入本身）。

坑：
  1. **不能用 round() 或 "%.1f"**：Python 用的是「四舍六入五成双」的银行家舍入，
     2.85 会变成 2.8。必须用 Decimal + ROUND_HALF_UP，而且要从字符串构造 Decimal，
     否则先转 float 已经引入二进制误差。
  2. 进位可能溢出到 10.0（例如 N = 999...），此时要重新规格化成 1.0*10^(c+1)，
     因为题目要求 a ∈ [1,9]。
  3. 只看第 3 位就能定舍入方向：第 3 位 >= 5 一定进位，< 5 一定不进位，
     后面还有多少位都不影响结果（HALF_UP 语义下）。
"""
import sys
from decimal import Decimal, ROUND_HALF_UP

s = sys.stdin.buffer.read().split()[0].decode()
c = len(s) - 1

head = (s + "00")[:3]                       # 题目保证 N >= 100，这里再补零以防万一
v = Decimal(head[0] + "." + head[1:]).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
if v >= 10:                                 # 9.95 这类进位溢出，重新规格化
    v = Decimal("1.0")
    c += 1

sys.stdout.write("{0}*10^{1}\n".format(v, c))

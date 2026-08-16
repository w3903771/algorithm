"""PIO14 单组_保留小数位数 —— 保留 3 位小数。

要点：不要用 round() 或 f"{x:.3f}"。Python 的浮点格式化用的是
      「四舍六入五成双」（banker's rounding），2.5 会变成 2 而不是 3。
      OJ 要的是数学意义上的四舍五入，正确做法是 Decimal + ROUND_HALF_UP，
      并且直接从**字符串**构造 Decimal，避免先转 float 引入二进制误差。
"""
from decimal import Decimal, ROUND_HALF_UP

n = Decimal(input().strip())
print(n.quantize(Decimal("0.000"), rounding=ROUND_HALF_UP))

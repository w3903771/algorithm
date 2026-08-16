"""PIO17 单组_spj判断浮点误差 —— 求圆面积，误差 1e-3 以内即可。

要点：用 math.pi 而不是自己写 3.14159；
      输出位数宁多勿少，多给几位小数不会错。
"""
import math

r = int(input())
print("%.6f" % (math.pi * r * r))

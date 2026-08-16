"""BISHI25 最大 FST 距离 —— 求 max |i^2 - j^2| + |A_i^2 - A_j^2|。

考点：曼哈顿距离最大值。令 x_i = i^2、y_i = A_i^2，要求的就是二维点集里
      最大的曼哈顿距离 max(|x_i-x_j| + |y_i-y_j|)。

      经典结论：|dx| + |dy| = max( (x_i+y_i)-(x_j+y_j), (x_j+y_j)-(x_i+y_i),
                                   (x_i-y_i)-(x_j-y_j), (x_j-y_j)-(x_i-y_i) )
      所以答案 = max( max(x+y) - min(x+y), max(x-y) - min(x-y) )，
      一次扫描即可，复杂度 O(n)。

规模：n <= 1e5，暴力两两枚举是 5e9 对，必然超时；O(n) 做法才可行。

坑：
  1. 下标 i 是 **1-based**（样例里 n=2、A=[4,3] 用的是 2^2-1^2=3）。
  2. A_i <= 1e9，A_i^2 <= 1e18，C++ 要小心 long long 溢出（和会到 ~2e18）；
     Python 是大整数，直接算。
  3. n = 1 时没有任何点对，答案为 0；上面的公式天然给出 0。
"""
import sys

data = sys.stdin.buffer.read().split()
n = int(data[0])
a = data[1:n + 1]

sp = []   # x + y
sm = []   # x - y
for i in range(1, n + 1):
    x = i * i
    y = int(a[i - 1]) ** 2
    sp.append(x + y)
    sm.append(x - y)

print(max(max(sp) - min(sp), max(sm) - min(sm)))

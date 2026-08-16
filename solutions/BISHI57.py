"""BISHI57 最大公因数与最小公倍数 —— 给定 a,b <= 2e9，输出 gcd 和 lcm。

这题考什么：
    欧几里得算法 + lcm(a,b) = a * b / gcd(a,b) 的恒等式。

数据规模与复杂度：
    单组数据，a,b <= 2e9。gcd 是 O(log min(a,b))，最多几十次取模。
    Python 直接用 math.gcd（C 实现的二进制 GCD），比手写递归快也不会爆栈。

坑在哪：
  1. lcm 要写成 a // g * b，**先除后乘**。写 a * b // g 时，
     a*b 最大 4e18 已经越过 int64 上界（9.22e18 勉强够，但换成更大范围就爆），
     养成先除后乘的习惯；Python 虽然不会溢出，但这个写法是通用正解；
  2. 两个数用一个空格隔开输出在同一行；
  3. Python 3.9 的 math.lcm 存在（3.9 新增），但为了展示恒等式这里手写。
"""
import math
import sys

a, b = map(int, sys.stdin.buffer.read().split()[:2])
g = math.gcd(a, b)
sys.stdout.write("%d %d\n" % (g, a // g * b))      # 先除后乘，避免中间量溢出

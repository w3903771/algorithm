"""BISHI26 构造C的歪 —— 给 a、b，求 c 使 {a,b,c} 排序后成等差数列。

这题考什么：
    等差数列的判定条件：三个数排序后 x <= y <= z 满足 x + z = 2y。
    给定两个数，第三个数有三种放法：放最小、放中间、放最大。
      - 放最大：c = 2*max(a,b) - min(a,b)，序列是 min, max, c，公差 max-min；
      - 放最小：c = 2*min(a,b) - max(a,b)，可能是负数；
      - 放中间：c = (a+b)/2，只在 a+b 为偶数时可行。
    只要选「放最大」这一种就恒有解，而且结果一定是正数，最省事。

数据规模与复杂度：
    a,b <= 1e6，单组数据，O(1)。答案量级最大 2e6，Python 不用担心溢出。

坑在哪：
    1. a == b 时 c = 2a - a = a，三个数全相等，公差 0 的等差数列，合法；
    2. 答案不唯一（样例里同一组输入给出了 1 和 4 两个答案），本地判定必须
       用 special judge，不能逐字符比对；
    3. 用 (a+b)//2 会在 a+b 为奇数时错，别偷懒。
"""
import sys

a, b = map(int, sys.stdin.buffer.read().split()[:2])
# 把 c 放在最大处：min, max, 2*max-min 是公差为 max-min 的等差数列
print(2 * max(a, b) - min(a, b))

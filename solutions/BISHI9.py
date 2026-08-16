"""BISHI9 田忌赛马 —— 三局两胜，田忌可任意排列自己的三匹马。

考点：暴力枚举（全排列）。规模只有 3 匹马，3! = 6 种出场顺序，直接枚举即可，
      不需要「田忌赛马」经典的贪心策略。复杂度 O(3! * 3) = O(1)。

坑：
  1. 「严格大于」才算赢，速度相等算平局，不计入任何一方的胜场。
  2. 三局两胜 = 赢的局数 >= 2，注意平局不能算赢。
"""
from itertools import permutations

v = list(map(int, input().split()))
a = list(map(int, input().split()))

# 枚举田忌三匹马的所有出场顺序，只要有一种能赢下至少两局即可
ok = any(sum(x > y for x, y in zip(p, v)) >= 2 for p in permutations(a))
print("Yes" if ok else "No")

"""BISHI24 谐距下标对 —— 统计满足 i < j 且 a_j - a_i = j - i 的下标对数量。

考点：把条件移项变成「同值配对」。
      a_j - a_i = j - i  <=>  a_j - j = a_i - i
      也就是说，令 b_i = a_i - i，答案就是所有 b 值相同的下标两两配对数之和：
      ∑ C(c, 2) = ∑ c*(c-1)/2。

规模：n <= 1e5，O(n^2) 的暴力枚举是 1e10 次必然超时；
      本做法只需一次计数，复杂度 O(n)。

坑：
  1. b_i 可能是负数（a_i >= 1 但 i 可以很大），所以用哈希表计数而不是数组下标。
  2. 答案量级最大是 C(1e5, 2) ≈ 5e9，C++ 必须 long long；Python 无需担心。
  3. 下标从 1 开始还是 0 开始不影响答案（整体平移不改变 b 的相等关系）。
"""
import sys
from collections import Counter

data = sys.stdin.buffer.read().split()
n = int(data[0])
cnt = Counter(int(v) - i for i, v in enumerate(data[1:n + 1]))
print(sum(c * (c - 1) // 2 for c in cnt.values()))

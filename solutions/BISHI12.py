"""BISHI12 元素方碑 —— 每次把 1 点能量在 a[i-1] 与 a[i+1] 之间搬运，问能否全部相等。

考点：发现不变量。能量每次移动的跨度都是 2（i-1 <-> i+1），所以**奇数位之间**、
      **偶数位之间**可以互相搬运，但奇数位的总和与偶数位的总和永远不变。
      又因为 i 取遍 2..n-1，奇/偶下标各自构成一条「相邻可互换」的链，
      链内任意重新分配都能做到（一次搬一格，不会出现负数）。
      因此充要条件就是：

        sum % n == 0，且 奇数位和 == v * 奇数位个数，偶数位和 == v * 偶数位个数
        （v = sum / n）

      判掉总和这一条后，只要两个分组和都恰好等于各自「应有」的份额即可。

规模：t <= 1e4，∑n <= 2e5，必须一次性读入全部 token 后用游标推进，
      每组 O(n)，总复杂度 O(∑n)。

坑：
  1. n = 1 和 n = 2 时一次操作都做不了。上面的公式天然覆盖：
     n=1 恒 YES；n=2 要求 a1 == a2。
  2. a_i 高达 1e9，n 高达 2e5，和会到 2e14，C++ 要开 long long，Python 无所谓。
"""
import sys

data = sys.stdin.buffer.read().split()
p = 0
t = int(data[p]); p += 1
out = []
for _ in range(t):
    n = int(data[p]); p += 1
    a = data[p:p + n]; p += n
    odd = sum(int(v) for v in a[0::2])   # 下标 1,3,5,...（0-based 的偶数位）
    even = sum(int(v) for v in a[1::2])  # 下标 2,4,6,...
    total = odd + even
    if total % n:
        out.append("NO")
        continue
    v = total // n
    c_odd = (n + 1) // 2
    out.append("YES" if odd == v * c_odd and even == v * (n - c_odd) else "NO")
sys.stdout.write("\n".join(out) + "\n")

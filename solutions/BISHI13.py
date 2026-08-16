"""BISHI13 九倍平方数 —— 可把数位 x 替换成 x^2（仅当 x^2 < 10），问能否被 9 整除。

考点：数字根（模 9）+ 有限枚举。
      x^2 < 10 只对 x ∈ {0,1,2,3} 成立：
        0 -> 0（数位和 +0）  1 -> 1（+0）
        2 -> 4（数位和 +2）  3 -> 9（数位和 +6）
      所以真正有用的操作只有两种：把某个 2 变成 4（和 +2），把某个 3 变成 9（和 +6）。
      设原数位和为 S，有 c2 个 2、c3 个 3，问是否存在 0<=i<=c2, 0<=j<=c3 使
      (S + 2i + 6j) % 9 == 0。

      因为 2i mod 9 的周期是 9（i 每加 9 回到原值），6j mod 9 的周期是 3，
      所以 i 只需枚举 0..min(c2, 8)，j 只需枚举 0..min(c3, 8)，
      每组最多 81 次判断，与串长无关。

规模：t <= 1e4，∑|n| <= 1e5，总复杂度 O(∑|n| + 81t)。

坑：
  1. 别去把整个 1e5 位的数转成 int 再取模，用数位和模 9 就够（9 的整除判定）。
  2. 4、5、6... 的平方都 >= 10，不能替换；1 和 0 替换了等于没换。
"""
import sys

data = sys.stdin.buffer.read().split()
t = int(data[0])
out = []
for k in range(1, t + 1):
    s = data[k]
    total = sum(s) - 48 * len(s)          # bytes 相加再减去 '0' 的偏移 = 数位和
    c2 = min(s.count(50), 8)              # b'2'
    c3 = min(s.count(51), 8)              # b'3'
    ok = any((total + 2 * i + 6 * j) % 9 == 0
             for i in range(c2 + 1) for j in range(c3 + 1))
    out.append("YES" if ok else "NO")
sys.stdout.write("\n".join(out) + "\n")

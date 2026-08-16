"""PIO16 单组_spj判断YES与NO —— 奇数 YES，偶数 NO。

要点：这是 special judge 题，大小写任意。
      判奇偶用 n & 1 比 n % 2 略快，效果相同。
"""
n = int(input())
print("YES" if n & 1 else "NO")

"""BISHI15 小红的夹吃棋 —— 3x3 棋盘，判断哪一方的棋子被「夹」。

考点：纯模拟。3x3 里能被夹住的只可能是「三连的中间」那格，
      横向只有每行的第 2 列，纵向只有每列的第 2 行，一共 6 个位置要检查。
      每组 O(1)，t 组总复杂度 O(t)。

判定：中间格是棋子（非 '.'），两侧都是棋子且与中间格不同色 —— 只有黑白两种颜色，
      所以「两侧相同且非 '.' 且不等于中间」就等价于「被对方两子夹住」。

坑：
  1. 双方都有子被夹 / 双方都没有 —— 都是平局 draw。
  2. 输出的是「对方获胜」：黑子（小红 '*'）被夹 -> 小紫赢 -> yukari；
     白子（小紫 'o'）被夹 -> 小红赢 -> kou。别弄反。
"""
import sys

data = sys.stdin.buffer.read().split()
t = int(data[0])
out = []
for i in range(t):
    g = [row.decode() for row in data[1 + 3 * i:4 + 3 * i]]
    black_eaten = white_eaten = False
    pos = [(g[r][1], g[r][0], g[r][2]) for r in range(3)]      # 横向三连的中间格
    pos += [(g[1][c], g[0][c], g[2][c]) for c in range(3)]     # 纵向三连的中间格
    for mid, left, right in pos:
        if mid != "." and left == right != "." and left != mid:
            if mid == "*":
                black_eaten = True
            else:
                white_eaten = True
    if black_eaten and not white_eaten:
        out.append("yukari")
    elif white_eaten and not black_eaten:
        out.append("kou")
    else:
        out.append("draw")
sys.stdout.write("\n".join(out) + "\n")

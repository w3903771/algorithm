"""BISHI15 小红的夹吃棋 —— 3x3 棋盘，判断哪一方的棋子被对方「夹」住。

这题考什么：
    把「规则描述」翻译成「有限个待检查位置」的模拟能力。
    被夹住的定义是「横向或纵向的三连中，中间那颗是对方的棋子」。
    3x3 的棋盘上三连只有 6 条：3 行 + 3 列，每条的中间格是固定的
    （第 r 行的中间格是 (r,1)，第 c 列的中间格是 (1,c)）。
    所以要检查的位置一共 6 个，把它们列出来逐个判断即可，无需搜索。

    判定条件可以再简化：棋盘上非空格只有黑白两色，所以
    「中间格非 '.'，两侧相等且非 '.'，且两侧与中间不同色」
    就等价于「中间那颗被对方两子夹住」——不必分别写黑被白夹、白被黑夹两套。

数据规模与复杂度：
    每组固定 6 次检查，O(1)；t 组总复杂度 O(t)。
    棋盘按行给出、每行是一个不含空格的字符串，所以整份输入
    split() 之后每个 token 恰好是一行棋盘，第 i 组占用 data[1+3i : 4+3i]。

坑在哪：
  1. 输出的是「**对方**获胜」，不是「被夹的一方获胜」：
     黑子（小红的 '*'）被夹 -> 小紫赢 -> 输出 yukari；
     白子（小紫的 'o'）被夹 -> 小红赢 -> 输出 kou。这一步最容易写反；
  2. 双方都有子被夹、双方都没有子被夹，两种情况都判平局 draw，
     所以两个布尔量要分别统计后再比较，不能一发现有子被夹就下结论；
  3. 角上的格子永远不会被夹（它不是任何三连的中间格），
     只检查 6 个中间格就是完备的，不需要遍历全部 9 格；
  4. 空格 '.' 既不能当被夹的对象，也不能当夹人的棋子，
     三个位置都要排除 '.' 才成立。

样例复核：
    第 3 组棋盘
        o*o
        *o*
        o*o
    每一行、每一列的中间格两侧都是异色棋子，黑白双方都有子被夹，
    按规则判平局，输出 draw，与样例一致。
"""
import sys

data = sys.stdin.buffer.read().split()
t = int(data[0])
out = []
for i in range(t):
    g = [row.decode() for row in data[1 + 3 * i:4 + 3 * i]]    # 本组的 3 行棋盘
    black_eaten = white_eaten = False
    # 把 6 条三连整理成 (中间格, 一侧, 另一侧) 的三元组，后面统一判定
    pos = [(g[r][1], g[r][0], g[r][2]) for r in range(3)]      # 横向三连的中间格
    pos += [(g[1][c], g[0][c], g[2][c]) for c in range(3)]     # 纵向三连的中间格
    for mid, left, right in pos:
        # 中间是棋子、两侧同色且非空、两侧与中间异色 —— 即中间这颗被对方夹住
        if mid != "." and left == right != "." and left != mid:
            if mid == "*":
                black_eaten = True                             # 黑子被夹
            else:
                white_eaten = True                             # 白子被夹
    # 只有一方被夹才分胜负，且赢家是对方
    if black_eaten and not white_eaten:
        out.append("yukari")
    elif white_eaten and not black_eaten:
        out.append("kou")
    else:
        out.append("draw")                                     # 都被夹或都没被夹
sys.stdout.write("\n".join(out) + "\n")

"""BISHI17 纸牌游戏 —— 双方各两张牌，翻牌顺序随机，数 Alex 获胜的顺序数。

考点：暴力枚举。Alex 的出牌顺序 2 种、Bob 的出牌顺序 2 种，一共 4 种「翻牌顺序」，
      每种模拟两回合即可。每组 O(4)，t <= 1e4 总复杂度 O(t)。

坑：
  1. 平分（各赢一局，或两局都是平手）不算 Alex 赢，只有严格赢的回合数更多才算。
  2. 单回合比分相等时**双方都不得分**，不要写成谁都赢。
  3. 统计的是「顺序数量」而不是概率，所以 4 种顺序即使牌面重复也各算一种
     （样例 10 10 2 2 的答案是 4 就是证据）。
"""
import sys

data = sys.stdin.buffer.read().split()
t = int(data[0])
out = []
for i in range(t):
    a1, a2, b1, b2 = map(int, data[1 + 4 * i:5 + 4 * i])
    cnt = 0
    for a in ((a1, a2), (a2, a1)):
        for b in ((b1, b2), (b2, b1)):
            win = sum(x > y for x, y in zip(a, b))
            lose = sum(x < y for x, y in zip(a, b))
            if win > lose:
                cnt += 1
    out.append(cnt)
sys.stdout.write("\n".join(map(str, out)) + "\n")

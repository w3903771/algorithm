"""BISHI19 乒乓球 —— 同一份 W/L 记录，分别按 11 分制和 21 分制切局并输出比分。

考点：线性扫描模拟。|s| <= 1e5，跑两遍，复杂度 O(|s|)。

规则：某方分数 >= 目标分（11 或 21）**且**双方分差 >= 2 时本局结束，比分清零开新局。

坑：
  1. 「>= 11 且领先 2 分」不是「等于 11」，13:11、15:13 这样的局是合法的。
  2. 记录读完后当前局若未结束也要输出比分 —— 包括**上一球刚好把一局打完、
     新局比分还是 0:0** 的情况，此时仍然要输出一行 "0:0"（NOIP 原题的标准做法）。
  3. 两部分之间要有一个空行分隔。
"""
import sys


def split_games(record, target):
    res, a, b = [], 0, 0
    for ch in record:
        if ch == "W":
            a += 1
        else:
            b += 1
        if (a >= target or b >= target) and abs(a - b) >= 2:
            res.append("%d:%d" % (a, b))
            a = b = 0
    res.append("%d:%d" % (a, b))   # 未打完的当前局（可能是 0:0）也要输出
    return res


s = sys.stdin.buffer.read().decode().strip()
out = split_games(s, 11) + [""] + split_games(s, 21)
sys.stdout.write("\n".join(out) + "\n")

"""BISHI133 最长不下降子序列 —— 求 LNDS 的长度。

这题考什么：
    LIS 的 **O(n log n)** 贪心 + 二分模板。
    维护数组 tails，tails[i] = 「长度为 i+1 的不下降子序列」结尾元素的**最小可能值**。
    tails 天然单调不减，新元素 x 来时：
      - 在 tails 里找第一个 **> x** 的位置 p，用 x 替换它（让同长度的结尾更小、更有潜力）；
      - 若不存在（x >= 所有元素），append，答案长度 +1。

    **等号位置是本题唯一的思维点**：
      | 目标 | 找的位置 | 函数 |
      | 最长**不下降**（允许相等） | 第一个 > x | `bisect_right` |
      | 最长**严格上升** | 第一个 >= x | `bisect_left` |
    记忆法：允许相等 ⇒ 相等的元素不该把 x 挤掉 ⇒ 越过它们 ⇒ right。

数据规模与复杂度：
    n <= 5e3，其实 O(n^2) 的朴素 DP（2.5e7）在 2 秒里也悬，
    而 O(n log n) 只有 6e4 次操作，稳。

坑在哪：
  1. tails **不是**答案序列本身，只是每个长度的最优结尾值，别拿它去还原方案；
  2. Python 3.9 的 `bisect` **不支持 key 参数**（3.10 才加），这里也用不上；
  3. n = 1 时答案是 1。
"""
import sys
from bisect import bisect_right


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    tails = []
    for tok in data[1:1 + n]:
        x = int(tok)
        p = bisect_right(tails, x)           # 不下降 -> right；严格上升 -> left
        if p == len(tails):
            tails.append(x)
        else:
            tails[p] = x
    sys.stdout.write("%d\n" % len(tails))


main()

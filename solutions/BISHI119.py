"""BISHI119 小红的01子序列构造（easy）—— 找一个子串，其中 "01" 子序列恰好 k 个。

这题考什么：
    双指针 + 单调性。设 f(l, r) = 子串 s[l..r] 中 "01" 子序列的个数
    （即每个 '1' 左边的 '0' 个数之和）。两条单调性：
      - 固定 l，f 关于 r **单调不减**（右边加字符只会增加配对）；
      - 固定 r，f 关于 l **单调不增**（左边删字符只会减少配对）。
    所以可以用「l 递增、r 只前进不后退」的双指针，总共 O(n)。

    增量维护（这是本题的实现核心）：窗口内记录 zeros（'0' 个数）、ones（'1' 个数）、pairs。
      - 右端加入字符 c：c=='1' 时 pairs += zeros, ones += 1；c=='0' 时 zeros += 1。
      - 左端删除字符 c（它是窗口最左边的）：
          c=='0'：它和窗口内**每一个 '1'** 都配过对，所以 pairs -= ones，zeros -= 1；
          c=='1'：它左边没有 '0'（它就是最左），pairs 不变，只有 ones -= 1。

数据规模与复杂度：
    n <= 2e5，k <= 1e10（最大可能值约 (n/2)^2 = 1e10，恰好卡在这里）。
    双指针 O(n)。枚举所有 O(n^2) 个区间是 4e10，必挂。

坑在哪：
  1. **删除左端 '1' 时 pairs 不变**——这一条最容易写错成 pairs -= zeros；
  2. r 指针一旦顶到 n 还不够 k，就可以直接判 -1 退出：
     再增大 l 只会让 pairs 更小；
  3. k >= 1，所以空窗口（pairs = 0）永远不是答案，不用担心 l > r 的退化；
  4. 答案不唯一，本题配了 solutions/_spj/BISHI119.py 做校验。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); k = int(data[1])
    s = data[2]
    ONE = 49                                 # ord('1')，直接比 bytes 的整数元素，省一次解码

    r = 0                                    # 窗口 [l, r]，r 为已加入的最右下标（1-indexed）
    zeros = ones = pairs = 0
    ans = None
    for l in range(1, n + 1):
        if r < l - 1:                        # 窗口被掏空了，重置
            r = l - 1
            zeros = ones = pairs = 0
        while r < n and pairs < k:
            c = s[r]                         # s[r] 是 1-indexed 的第 r+1 个字符
            r += 1
            if c == ONE:
                pairs += zeros
                ones += 1
            else:
                zeros += 1
        if pairs == k:
            ans = (l, r)
            break
        if r >= n and pairs < k:             # 右端已到头仍不够，l 再往右只会更小
            break
        if r >= l:                           # 弹出左端字符 s[l]
            if s[l - 1] == ONE:
                ones -= 1
            else:
                zeros -= 1
                pairs -= ones
    if ans is None:
        sys.stdout.write("-1\n")
    else:
        sys.stdout.write("%d %d\n" % ans)


main()

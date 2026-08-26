# 来源: 牛客 · 面试必刷TOP101　中等
# 链接: https://www.nowcoder.com/practice/f33f5adc55f444baa0e0ca87ad8a6aac
# 判题: 核心代码模式
# 签名: LCS(str1: string、str2: string) -> string

"""BM66 最长公共子串 —— 二分答案 + 滚动哈希，把 O(n*m) 的填表压到 O((n+m) log n)。

这题考什么：
    先认清它与最长公共**子序列**（BM65）的差别：子串必须**连续**，中间不许跳字符。
    教科书解法是二维 DP：

        状态定义：dp[i][j] = 以 str1[i-1]、str2[j-1] 为**结尾**的公共子串长度。
        转移方程：

            str1[i-1] == str2[j-1]:  dp[i][j] = dp[i-1][j-1] + 1
            否则:                    dp[i][j] = 0        连续性一旦断开就归零

        全表取最大值，记下结尾位置再回切一段就是答案。
        「不匹配即归零」这一条正是子串与子序列的分水岭：
        子序列允许 max(dp[i-1][j], dp[i][j-1]) 继承，子串不允许。

    本题 |str| 可达 5000，这张表有 2.5e7 格，CPython 每秒千万次量级的循环填不完（见下）。
    换成「二分答案 + 字符串哈希」，只用 O((n+m) log n) 就能定位同一个答案：

      1. **单调性**：存在长度为 L 的公共子串，就必然存在长度为 L-1 的
         （从它掐掉一个字符即可），所以「是否存在长度 L 的公共子串」关于 L 单调，
         可以对答案二分，见 docs/basic/binary-search.md。
      2. **判定 check(L)**：把 str1 的所有长度 L 的窗口哈希丢进字典，
         再扫 str2 的每个长度 L 的窗口去查表。用多项式滚动哈希预处理前缀，
         任意窗口的哈希 O(1) 取出，单次判定 O(n + m)，
         哈希本身见 docs/ds/hash.md。
      3. **真串比对兜底**：哈希命中只当作「候选」，随后用切片做一次真正的字符串比较。
         于是正确性完全不依赖哈希的质量——碰撞只会白比一次，绝不会答错。
         正因为有这道兜底，底数取固定质数 131 就够，不需要随机化；
         教学仓库里也不放随机数，同样的输入每次都该跑出同样的过程。

数据规模与复杂度：
    |str1|, |str2| <= 5000，时限 2 秒（其他语言）。
      - 二维 DP：2.5e7 格，即 2.5e7 次 Python 级迭代。判题机比本机慢数倍，
        按 3~4 倍余量折算，这个量级在 2 秒里没有指望，所以被否决。
      - 本解法：二分至多 log2(5000) 约 13 轮，每轮 O(n + m) = 1e4 次操作，
        合计 1.3e5 次，外加一次 O(n + m) 的前缀哈希预处理。
        时间 O((n + m) log min(n, m))，空间 O(n + m)（前缀哈希、幂表与哈希字典）。
    题面写的 O(n^2) 是**上界**不是要求，跑得更快不违规。

坑在哪：
  1. 答案要的是子串本身而不是长度，所以 check 返回的是起点下标；
     只记长度就还原不出该切哪一段。best_start 与 best_len 必须成对更新，
     否则二分继续往上探失败后会拿到别的长度的起点。
  2. 二分的边界写法是「成功就记录并把下界抬到 mid+1，失败就把上界压到 mid-1」，
     循环条件 lo <= hi。记录动作必须放在成功分支里，
     退出时 best_len 才是最后一次成功的长度。
  3. 两串没有公共字符时 check(1) 就失败，best_len 保持 0，返回空串。
     题面声明最长公共子串存在且唯一，这条出口是防御性的。
  4. 前缀哈希取子段用的是减法，减完可能是负数。Python 的 % 永远返回非负余数，
     所以两侧算出的键一定一致；在 C++ / Java 里必须手动加一个模数再取模，
     照搬这段代码到那些语言会因负余数而查不到本该命中的候选。
  5. 模数取梅森素数 2^61 - 1 而非 2^64：Python 的整数没有溢出回绕，
     取一个足够大的素数是为了把碰撞概率压到可以忽略，不是为了迁就字长。
  6. 幂表 pw 要开到 max(n, m)，两串各自的窗口都要用它；只按 min 开会越界。

样例复核：
    str1 = "1AB2345CD"、str2 = "12345EF"。二分区间起始 [1, 7]：
    check(4) 命中 "2345" 起点 3，抬下界；check(6)、check(5) 均失败，压上界；
    最终 best_len = 4、best_start = 3，切出 "2345"，与期望输出一致。
"""
from typing import List, Optional

_MOD = (1 << 61) - 1                       # 梅森素数；Python 大整数无溢出，取大模数纯为压碰撞率


class Solution:
    def LCS(self, str1: str, str2: str) -> str:
        n, m = len(str1), len(str2)
        if n == 0 or m == 0:
            return ""                      # 有一方为空则无公共子串
        # 底数取固定质数即可：命中候选后还有**真串比对**兜底，
        # 哈希只负责筛候选，碰撞至多多比几次，不会让答案出错
        base = 131
        # 幂表：pw[k] = base^k mod _MOD，用来把前缀哈希对齐到同一位数
        pw = [1] * (max(n, m) + 1)         # 两串共用，长度按较长的那个开
        for i in range(1, len(pw)):
            pw[i] = pw[i - 1] * base % _MOD
        # 前缀哈希：h[i] 是 str[:i] 的哈希，于是窗口 [i, i+L) 的哈希 = h[i+L] - h[i]*pw[L]
        h1 = [0] * (n + 1)
        for i, c in enumerate(str1):
            h1[i + 1] = (h1[i] * base + ord(c)) % _MOD
        h2 = [0] * (m + 1)
        for i, c in enumerate(str2):
            h2[i + 1] = (h2[i] * base + ord(c)) % _MOD

        def check(length: int) -> int:
            """存在长度为 length 的公共子串就返回它在 str1 中的起点，否则 -1。"""
            p = pw[length]                 # 本轮窗口长度固定，幂只取一次
            table = {}
            # str1 的每个窗口按哈希分桶；同一个键挂多个起点，留给真串比对逐个验
            for i in range(n - length + 1):
                table.setdefault((h1[i + length] - h1[i] * p) % _MOD, []).append(i)
            for j in range(m - length + 1):
                # 减法结果可能为负，Python 的 % 返回非负余数，与建表时的算法完全一致
                starts = table.get((h2[j + length] - h2[j] * p) % _MOD)
                if starts is not None:
                    seg = str2[j:j + length]
                    for i in starts:                     # 真串比对：碰撞只是白比，绝不误判
                        if str1[i:i + length] == seg:
                            return i
            return -1

        # 对答案长度二分：长度 L 可行 => L-1 也可行（掐掉一个字符），判定关于 L 单调
        lo, hi = 1, min(n, m)
        best_start, best_len = 0, 0        # 全程无解时保持 0，最后切出空串
        while lo <= hi:
            mid = (lo + hi) >> 1
            start = check(mid)
            if start >= 0:
                best_start, best_len = start, mid        # 起点与长度必须成对记下
                lo = mid + 1                             # 这个长度可行，试更长的
            else:
                hi = mid - 1                             # 不可行，更长的更不可行
        return str1[best_start:best_start + best_len]

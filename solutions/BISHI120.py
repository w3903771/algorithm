"""BISHI120 ？？？ —— 把 s 里的 '?' 全部填成小写字母，使 t 成为 s 的子序列。

这题考什么：
    子序列匹配的**贪心 + 双指针**，以及「贪心为什么对」的证明习惯。

    做法：i 扫 s，j 指向 t 中待匹配的字符。
      - s[i] == '?'：如果 t 还没匹配完，就把它填成 t[j] 并 j += 1（用掉这个万能位）；
        否则随便填一个 'a'；
      - s[i] 是字母：如果它正好等于 t[j]，就 j += 1；否则跳过。
    扫完看 j 是否等于 |t|。

    正确性（交换论证）：**最左匹配一定最优**。若存在合法方案在位置 p 匹配 t[j]，
    而贪心在更靠左的 p' <= p 匹配 t[j]，把该方案的匹配点换到 p' 后剩余部分只会更宽松；
    '?' 能变成任意字符，所以「遇到 '?' 就用掉」不会让后面变差。

数据规模与复杂度：
    T <= 1e4，Σ|s| <= 2e5，总复杂度 O(Σ|s|)。

坑在哪：
  1. 多余的 '?' 也**必须**填成某个字母（不能留 '?'），题目要求输出的是完整字符串；
  2. 只有 j < |t| 时才拿 '?' 去匹配，否则会下标越界；
  3. 输出格式是先一行 YES/NO，YES 后**再输出一行**结果串；
  4. 答案不唯一（多余的 '?' 填什么都行），本题配了 solutions/_spj/BISHI120.py 校验。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    T = int(data[0])
    out = []
    push = out.append
    p = 1
    for _ in range(T):
        s = bytearray(data[p]); t = data[p + 1]
        p += 2
        lt = len(t)
        j = 0
        for i in range(len(s)):
            c = s[i]
            if c == 63:                      # ord('?')
                if j < lt:
                    s[i] = t[j]              # 万能位优先用来匹配 t
                    j += 1
                else:
                    s[i] = 97                # ord('a')，随便填
            elif j < lt and c == t[j]:
                j += 1
        if j == lt:
            push("YES")
            push(s.decode())
        else:
            push("NO")
    sys.stdout.write("\n".join(out) + "\n")


main()

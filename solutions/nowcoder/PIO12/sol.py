"""PIO12 单组_二维字符数组 —— n 行 m 列的小写字母矩阵，行和列都倒置后输出。

这题考什么：
    输入形态：单组数据，带两个前导数量，数据本体是 n 行不含空格的字符串。

    「行和列都倒置」听起来像两个操作，其实就是把整个矩阵旋转 180 度：
    列倒置 = 每一行内部左右翻转，即 r[::-1]；
    行倒置 = 行与行之间上下翻转，即 reversed(rows)。
    两者作用在不同维度上，互不干扰，先做哪个都一样。

    每行都不含空格，所以 split() 之后一行恰好是一个 token：
    跳过开头的 n 和 m 两个 token，第 i 行就是 data[2 + i]。
    这个对应关系完全依赖「行内无空白」，与 PIO11 是同一个前提。

    reversed(rows) 返回的是反向迭代器而不是新列表，
    配合生成器表达式喂给 join，全程不多建一份行的副本。

为什么输出用一次 write：
    n 最大 1e3，逐行 print 就是一千次输出调用；
    把所有行 join 成一整块字符串一次写出只有一次调用。
    对于结果本身就是多行文本的题，join 还顺便保证了行与行之间只有一个换行符。

数据规模与复杂度：
    n, m <= 1e3，字符总数最多 1e6，仅含小写英文字母。
    时间 O(n * m)，空间 O(n * m)。

坑在哪：
  1. 倒置不是转置。zip(*rows) 得到的是行列互换（m 行 n 列），
     与本题要求的旋转 180 度完全是两回事，样例就能把它区分开。
  2. 每行是 bytes，必须 decode 成 str；否则 join 一个 bytes 列表会抛 TypeError。
  3. 数据从下标 2 开始，前两个 token 是 n 和 m。起点写成 1 会把 m 当成第一行。
  4. 末尾要补一个行尾换行，否则最后一行缺换行符，部分判定环境会报格式错误。

样例复核：
    3 行 4 列的 abcd / efgh / ijkl，每行翻转得 dcba / hgfe / lkji，
    再把行序倒过来是 lkji / hgfe / dcba，与样例输出一致。
"""
import sys

data = sys.stdin.buffer.read().split()
n, m = int(data[0]), int(data[1])         # 数据从下标 2 开始
# 行内无空格，故一行恰好是一个 token；bytes 要 decode 成 str 才能拼接
rows = [data[2 + i].decode() for i in range(n)]
# r[::-1] 翻转行内字符（列倒置），reversed(rows) 翻转行序（行倒置），合起来是旋转 180 度
sys.stdout.write("\n".join(r[::-1] for r in reversed(rows)) + "\n")

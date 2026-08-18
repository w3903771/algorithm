"""BISHI92 【模板】前缀函数（KMP）—— 对每组字符串输出其全部 π 值。

这题考什么：
    KMP（Knuth-Morris-Pratt，利用已匹配信息避免回退主串的字符串匹配算法）
    的前缀函数模板。π[i] = s[0..i] 的「最长真前缀 = 真后缀」的长度。
    完整推导见 docs/part6-字符串/71-字符串匹配KMP.md。

    递推的核心：算 π[i] 时，候选长度只能是
        π[i-1], π[π[i-1]-1], π[π[π[i-1]-1]-1], ...
    这条「失配链」上的值。用一个游标 k 记住当前候选长度，
    只要 s[k] != s[i] 就沿链回退 k = π[k-1]，匹配上就 k += 1。
    虽然内层是 while，但 k 每轮最多 +1、回退总量不超过 +1 的总量，
    **均摊 O(n)**（这也是「测试点 11~15 只用一种字符」想卡的地方：
    aaaa... 时 k 一路 +1 从不回退，反而是最快的情况；
    真正的最坏是 aaaab 这类，但均摊仍是线性）。

数据规模与复杂度：
    T <= 2e6，Σn <= 2e6。总复杂度 O(Σn)。

Python 的坑（本题必看）：
  1. **IO 是本题最大的瓶颈**：输入约 2e6 字符，输出是 2e6 个整数（约 4~14 MB）。
     必须 sys.stdin.buffer.read().split() 一次读完，
     输出 "\n".join 一次性 write。逐行 print 会慢几十倍；
  2. 在 bytes 上做索引得到的是 int，比较 int 比比较单字符 str 更快，
     所以全程用 bytes，不做 decode；
  3. 把 s、pi 绑定成局部变量（函数内），CPython 访问局部变量比全局快很多；
  4. " ".join(map(str, pi)) 里的 map(str, ...) 走 C 层循环，
     比列表推导 [str(x) for x in pi] 略快。

坑在哪：
    每组数据的格式是「先一个整数 n，再一个长度 n 的字符串」，两者在同一行，
    但按 token 读就完全不用关心换行位置。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    out = []
    p = 1
    for _ in range(t):
        n = int(data[p]); s = data[p + 1]; p += 2    # 每组两个 token：长度与串本身
        pi = [0] * n
        k = 0                           # 当前候选的「最长相等真前后缀」长度
        for i in range(1, n):           # pi[0] 恒为 0：真前缀不能是整个串
            c = s[i]
            while k and s[k] != c:      # 沿失配链回退，均摊 O(1)
                k = pi[k - 1]
            if s[k] == c:               # 对上了就把候选长度延长一位
                k += 1
            pi[i] = k                   # k 退到 0 仍不匹配时，pi[i] 自然是 0
        out.append(" ".join(map(str, pi)))          # 每组结果先拼成一整行
    sys.stdout.write("\n".join(out) + "\n")


main()

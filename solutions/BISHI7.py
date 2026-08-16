"""BISHI7 字符串哈希 —— 求 N 个字符串里有多少个不同的。

这题考什么：
    题目名叫「字符串哈希」，C++ 里的标准做法是给每个串算一个多项式哈希
    （或双哈希）再去重，避免 O(N^2 * |s|) 的两两比较。
    Python 里 str/bytes 本身就是可哈希的，set 内部就是哈希表，而且哈希
    计算是 C 实现的 SipHash，比手写多项式哈希又快又不会被卡冲突——
    所以直接 len(set(...)) 就是本题的正解，不需要自己造轮子。

数据规模与复杂度：
    N <= 1e4，|s| <= 1500，总字符量最多 1.5e7，一次性读入约 15MB，
    空间限制 512MB 完全放得下。
    建 set 的复杂度 O(总字符量)（每个串哈希一次 + 冲突时比较一次），
    比两两比较的 O(N^2 |s|) = 1.5e11 快了 4 个数量级。

坑在哪：
    1. **区分大小写**，不能 lower()：样例里 Hello / hello / HELLO 算 3 个不同串；
    2. 串里只有数字和大小写字母（无空格），所以可以放心用 split() 按空白切
       token，不必逐行 readline；
    3. 只取前 N 个 token，防止输入尾部有多余空行/脏数据；
    4. 直接对 bytes 去重，省掉 1e4 次 decode。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    sys.stdout.write(str(len(set(data[1:1 + n]))) + "\n")


main()

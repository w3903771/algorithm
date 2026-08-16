"""BISHI110 【模板】静态区间和（前缀和）—— n 个数、q 次区间求和查询。

这题考什么：
    前缀和模板。令 S[k] = a_1 + ... + a_k（S[0] = 0），则
        sum(l..r) = S[r] - S[l-1]
    预处理 O(n)，每次查询 O(1)。

数据规模与复杂度：
    n, q <= 1e6。O(n + q)。
    暴力每次扫区间是 1e12 必挂；线段树 / 树状数组能做但完全没必要
    （没有修改操作，前缀和是最优解，常数也最小）。

Python 的坑（本题的真正难点全在这里）：
  1. **IO 就是瓶颈**：输入约 3e6 个整数（≈ 20 MB 文本），输出 1e6 行。
     必须 sys.stdin.buffer.read().split() 一次读完，
     输出 "\n".join 拼成一整块再一次 write；
     用 input() / print() 会慢一两个数量级；
  2. 前缀和用 **itertools.accumulate**（C 层循环），
     比 Python 的 `for` 累加快好几倍；
  3. `list(map(int, ...))` 也是 C 层循环，比列表推导快；
  4. 询问的 l、r 直接用 `int()` 转，配合游标推进；
     这里把 l、r 的 token 用切片一次性取出再 map(int) 转换，
     再用 zip 配对，避免 1e6 次的下标算术。

坑在哪：
  1. a_i 可以是负数，前缀和不再单调，但公式不受影响；
  2. 和的绝对值最大 1e6 * 1e9 = 1e15，C++ 必须 long long；Python 无忧；
  3. 下标是 1-based，S 要多留一位 0。
"""
import sys
from itertools import accumulate


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); q = int(data[1])
    a = map(int, data[2:2 + n])
    S = [0]
    S.extend(accumulate(a))                    # S[k] = a_1 + ... + a_k

    rest = data[2 + n:2 + n + 2 * q]
    ls = map(int, rest[0::2])
    rs = map(int, rest[1::2])
    out = [str(S[r] - S[l - 1]) for l, r in zip(ls, rs)]
    sys.stdout.write("\n".join(out) + "\n")


main()

"""BISHI4 【模板】集合操作 —— 插入/删除/存在性/大小/前驱/后继。

这题考什么：
    带前驱后继查询的有序集合。C++ 直接 std::set，Python 没有内置有序集合，
    也**不能**用第三方 sortedcontainers（牛客判题机没装）。必须自己造。

数据规模与复杂度：
    n <= 1e5，值域 0 <= x <= 1e6（关键！值域小且固定）。
    值域小 => 可以开值域数据结构，不用离散化、不用平衡树。
    这里用「两级位图（bitset + summary）」：
      - 把 [0, 1e6] 切成每块 1024 个值，共 977 块，每块用一个 1024 位的
        Python 大整数当位图；再用一个 977 位的 summary 大整数标记哪些块非空。
      - 插入/删除/存在性 O(1)；
      - 前驱/后继：先在本块内用位运算取「低于 r 的最高位 / 高于 r 的最低位」，
        本块没有就去 summary 里找相邻的非空块，同样是一次位运算，O(1)。
    总复杂度 O(n)，每次操作只做几次 128 字节大整数的位运算。
    对比树状数组 + 倍增（O(n log V)，2e6 次纯 Python 循环迭代）快一个数量级，
    这在「其他语言 2 秒」的限制下很重要——Python 里应当尽量把循环压进
    C 实现的大整数运算里。

位运算取前驱/后继的套路：
    - 低位掩码 v & ((1<<r) - 1) 保留 < r 的位，最高位 = bit_length() - 1；
    - lowbit 取最低位：v & -v，其位置 = (v & -v).bit_length() - 1。

坑在哪：
    1. 前驱是「严格小于 x 的最大值」，后继是「严格大于 x 的最小值」，
       都不含 x 本身，x 在不在集合里都无所谓；
    2. 操作 4 这一行**只有一个数字**（其余操作是两个），所以按行解析而不是
       按 token 游标盲读，才不会错位；
    3. 插入重复元素 / 删除不存在元素都要静默忽略，且不能把 size 算错；
    4. 前驱后继不存在输出 -1，不是空行。
"""
import sys

BITS = 1024                      # 每块 1024 个值
NBLK = 10 ** 6 // BITS + 1       # 977 块，覆盖 [0, 1e6]


def main() -> None:
    data = sys.stdin.buffer.read().split(b"\n")
    n = int(data[0])
    blk = [0] * NBLK             # blk[i] 的第 r 位 = 值 i*1024+r 是否在集合中
    summ = 0                     # summ 的第 i 位 = 第 i 块是否非空
    size = 0
    out = []

    for k in range(1, n + 1):
        p = data[k].split()
        op = p[0]

        if op == b"4":           # 集合大小（这一行没有 x）
            out.append(str(size))
            continue

        x = int(p[1])
        b, r = divmod(x, BITS)

        if op == b"1":                                  # 插入
            if not (blk[b] >> r) & 1:
                blk[b] |= 1 << r
                summ |= 1 << b
                size += 1
        elif op == b"2":                                # 删除
            if (blk[b] >> r) & 1:
                v = blk[b] & ~(1 << r)
                blk[b] = v
                if v == 0:
                    summ &= ~(1 << b)                   # 整块空了，从 summary 摘掉
                size -= 1
        elif op == b"3":                                # 存在性
            out.append("YES" if (blk[b] >> r) & 1 else "NO")
        elif op == b"5":                                # 前驱：< x 的最大值
            low = blk[b] & ((1 << r) - 1)               # 本块中小于 x 的部分
            if low:
                out.append(str(b * BITS + low.bit_length() - 1))
            else:
                s = summ & ((1 << b) - 1)               # 更左边的非空块
                if s:
                    bb = s.bit_length() - 1
                    out.append(str(bb * BITS + blk[bb].bit_length() - 1))
                else:
                    out.append("-1")
        else:                                           # 6 后继：> x 的最小值
            hi = blk[b] >> (r + 1)                      # 本块中大于 x 的部分
            if hi:
                out.append(str(x + 1 + (hi & -hi).bit_length() - 1))
            else:
                s = summ >> (b + 1)                     # 更右边的非空块
                if s:
                    bb = b + 1 + (s & -s).bit_length() - 1
                    v = blk[bb]
                    out.append(str(bb * BITS + (v & -v).bit_length() - 1))
                else:
                    out.append("-1")

    sys.stdout.write("\n".join(out) + "\n")


main()

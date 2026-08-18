"""BISHI4 【模板】集合操作 —— 插入/删除/存在性/大小/前驱/后继。

这题考什么：
    带前驱后继查询的有序集合。C++ 直接 std::set，Python 没有内置有序集合，
    也**不能**用第三方 sortedcontainers（牛客判题机没装）。必须自己造。

    造法的思路是：把「集合里有哪些值」压成一个大整数的二进制位
    （第 k 位为 1 表示值 k 在集合里），这样「找小于 x 的最大元素」就变成
    「取某个整数中低于第 r 位的最高位」，一次位运算即可。
    位数太多时单个大整数的运算会变慢，所以按 1024 位分块，再用一个
    summary（摘要）整数记录哪些块非空，两级定位。
    位运算基础见 docs/part4-基础算法/46-位运算.md，
    离散化见 docs/part4-基础算法/41-桶计数与离散化.md，
    有序集合的其他实现见 docs/part3-数据结构/34-集合与多重集合.md。

数据规模与复杂度：
    n <= 1e5。题面写的是 0 <= x <= 1e6，但**实测数据里有负数**（见下面「坑」第 5 条），
    所以不能直接开值域数组。好在这题是离线的——n 行操作可以一次读完，
    于是先把所有出现过的 x 离散化（去重排序，至多 1e5 个），
    后面所有操作都在「下标」这个 [0, m) 的小值域上做，从此与原始值域无关。

    离散化之后用「两级位图（bitset + summary）」：
      - 把 [0, m) 切成每块 1024 个下标，共 <= 98 块，每块用一个 1024 位的
        Python 大整数当位图；再用一个 98 位的 summary 大整数标记哪些块非空。
      - 插入/删除/存在性 O(1)；
      - 前驱/后继：先在本块内用位运算取「低于 r 的最高位 / 高于 r 的最低位」，
        本块没有就去 summary 里找相邻的非空块，同样是一次位运算，O(1)。
    总复杂度 O(n log n)（瓶颈是排序），每次操作只做几次大整数位运算。
    对比树状数组 + 倍增（O(n log V)，2e6 次纯 Python 循环迭代）快一个数量级，
    这在「其他语言 2 秒」的限制下很重要——Python 里应当尽量把循环压进
    C 实现的大整数运算里。

    离散化在这里还白捡一个好处：前驱/后继的答案必然是**某个插入过的值**，
    而插入过的值一定在离散化表里，所以在下标上找完再映射回去，答案不会丢。

位运算取前驱/后继的套路：
    - 低位掩码 v & ((1<<r) - 1) 保留 < r 的位，最高位 = bit_length() - 1；
    - lowbit 取最低位：v & -v，其位置 = (v & -v).bit_length() - 1。

坑在哪：
    1. 前驱是「严格小于 x 的最大值」，后继是「严格大于 x 的最小值」，
       都不含 x 本身，x 在不在集合里都无所谓；
    2. 操作 4 这一行**只有一个数字**（其余操作是两个），所以按行解析而不是
       按 token 游标盲读，才不会错位；
    3. 插入重复元素 / 删除不存在元素都要静默忽略，且不能把 size 算错；
    4. 前驱后继不存在输出 -1，不是空行；
    5. **实测数据里的 x 会超出题面写的 0 <= x <= 1e6，出现负数**。
       按题面范围直接开值域位图，负数会在 divmod(x, 1024) 得到负的块号，
       随后在 `1 << b` 上抛 ValueError: negative shift count。
       离散化不依赖值域，天然免疫这一类越界，是最省心的写法。

样例复核：
    示例 2 的 {5,10,20} 离散化后下标为 5->0、10->1、15->2、20->3
    （15 只在询问里出现，同样进表）。查 15 的前驱：本块中低于第 2 位的部分
    是 0b011，最高位是第 1 位，映射回原值 10；查后继：高于第 2 位的部分
    最低位落在第 3 位，映射回 20。与样例一致。
"""
import sys

BITS = 1024                      # 每块 1024 个下标


def main() -> None:
    data = sys.stdin.buffer.read().split(b"\n")
    n = int(data[0])

    # 第一遍：把操作读出来，同时收集所有出现过的 x 用于离散化
    ops = []
    vals = []
    for k in range(1, n + 1):
        p = data[k].split()
        op = p[0]
        if op == b"4":           # 这一行没有 x
            ops.append((4, 0))
        else:
            x = int(p[1])
            ops.append((int(op), x))
            vals.append(x)

    uniq = sorted(set(vals))                     # 下标 -> 原值
    rank = {v: i for i, v in enumerate(uniq)}    # 原值 -> 下标
    nblk = len(uniq) // BITS + 1

    blk = [0] * nblk             # blk[i] 的第 r 位 = 下标 i*1024+r 是否在集合中
    summ = 0                     # summ 的第 i 位 = 第 i 块是否非空
    size = 0
    out = []

    for op, x in ops:
        if op == 4:                                     # 集合大小
            out.append(str(size))
            continue

        i = rank[x]
        b, r = divmod(i, BITS)

        if op == 1:                                     # 插入
            if not (blk[b] >> r) & 1:
                blk[b] |= 1 << r
                summ |= 1 << b
                size += 1
        elif op == 2:                                   # 删除
            if (blk[b] >> r) & 1:
                v = blk[b] & ~(1 << r)
                blk[b] = v
                if v == 0:
                    summ &= ~(1 << b)                   # 整块空了，从 summary 摘掉
                size -= 1
        elif op == 3:                                   # 存在性
            out.append("YES" if (blk[b] >> r) & 1 else "NO")
        elif op == 5:                                   # 前驱：< x 的最大值
            low = blk[b] & ((1 << r) - 1)               # 本块中小于 x 的部分
            if low:
                out.append(str(uniq[b * BITS + low.bit_length() - 1]))
            else:
                s = summ & ((1 << b) - 1)               # 更左边的非空块
                if s:
                    bb = s.bit_length() - 1
                    out.append(str(uniq[bb * BITS + blk[bb].bit_length() - 1]))
                else:
                    out.append("-1")
        else:                                           # 6 后继：> x 的最小值
            hi = blk[b] >> (r + 1)                      # 本块中大于 x 的部分
            if hi:
                out.append(str(uniq[i + 1 + (hi & -hi).bit_length() - 1]))
            else:
                s = summ >> (b + 1)                     # 更右边的非空块
                if s:
                    bb = b + 1 + (s & -s).bit_length() - 1
                    v = blk[bb]
                    out.append(str(uniq[bb * BITS + (v & -v).bit_length() - 1]))
                else:
                    out.append("-1")

    sys.stdout.write("\n".join(out) + "\n")


main()

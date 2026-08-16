"""BISHI5 【模板】多重集合操作 —— 插入/删除一个/计数/总大小/前驱/后继。

这题考什么：
    可重复元素的有序集合（C++ 的 std::multiset）。Python 既没有内置有序
    集合，也不能用第三方 sortedcontainers（牛客判题机没有），必须自己造。

为什么不用别的写法：
    - Counter + 每次排序：单次查询 O(k log k)，1e5 次直接爆炸；
    - 堆 + 懒删除：只能取最值，无法回答任意 x 的前驱后继；
    - 树状数组 + 倍增：O(n log V) 正确，但 1e5 * 21 ≈ 2e6 次纯 Python
      循环迭代，在「其他语言 2 秒」的限制下偏险。
    所以选下面这个：**计数字典 + 两级位图**。

数据规模与复杂度：
    n <= 1e5，|x| <= 1e6 => 平移 +1e6 后值域固定为 [0, 2e6]，值域小，
    可以直接开值域结构，不需要离散化（而且是在线操作，也不方便离线离散化）。
      - cnt: dict，记每个值出现几次（多重性），最多 1e5 个 key；
      - blk: 1954 个 1024 位大整数组成的位图，只记「该值是否出现过（次数>0）」；
      - summ: 1954 位大整数，标记哪些块非空。
    插入/删除/计数/大小都是 O(1)；前驱后继靠位运算在块内 + summary 里各
    定位一次，也是 O(1)。总复杂度 O(n)，常数是几次 C 层大整数位运算。

    位图与计数分离是关键：多重性交给 dict，有序性交给位图，
    删除时只有「计数从 1 掉到 0」才需要清位图。

坑在哪：
    1. 前驱/后继是**严格**小于/大于 x，且与 x 自身在不在集合里无关；
    2. 前驱后继输出的是原始值，别忘了减回偏移量 OFFSET；
    3. x 可以是负数（|x| <= 1e6），必须平移后再进位图；
    4. 删除不存在的元素要静默忽略，且不能把 total 减成负数；
    5. 操作 4 在本题也带一个占位参数（样例里是 `4 0`），题面写的是每行两个
       整数——这里按行解析，`4` 单独一行也能正确处理，两种格式都吃得下；
    6. 操作 3 查的是「出现次数」（可能是 0），操作 4 查的是含重复的总个数。
"""
import sys

OFFSET = 10 ** 6                        # 把 [-1e6, 1e6] 平移到 [0, 2e6]
BITS = 1024
NBLK = (2 * 10 ** 6) // BITS + 1        # 1954 块


def main() -> None:
    data = sys.stdin.buffer.read().split(b"\n")
    n = int(data[0])
    cnt = {}                            # 值 -> 出现次数（只存 > 0 的）
    blk = [0] * NBLK                    # 位图：该值是否存在
    summ = 0                            # 哪些块非空
    total = 0                           # 含重复的元素总数
    out = []

    for k in range(1, n + 1):
        p = data[k].split()
        op = p[0]

        if op == b"4":                                  # 总个数（含重复）
            out.append(str(total))
            continue

        x = int(p[1]) + OFFSET
        b, r = divmod(x, BITS)

        if op == b"1":                                  # 插入一个
            c = cnt.get(x, 0)
            cnt[x] = c + 1
            total += 1
            if c == 0:                                  # 第一次出现才点亮位图
                blk[b] |= 1 << r
                summ |= 1 << b
        elif op == b"2":                                # 删除一个
            c = cnt.get(x, 0)
            if c:
                total -= 1
                if c == 1:                              # 归零才熄灭位图
                    del cnt[x]
                    v = blk[b] & ~(1 << r)
                    blk[b] = v
                    if v == 0:
                        summ &= ~(1 << b)
                else:
                    cnt[x] = c - 1
        elif op == b"3":                                # 该值出现次数
            out.append(str(cnt.get(x, 0)))
        elif op == b"5":                                # 前驱：< x 的最大值
            low = blk[b] & ((1 << r) - 1)
            if low:
                out.append(str(b * BITS + low.bit_length() - 1 - OFFSET))
            else:
                s = summ & ((1 << b) - 1)
                if s:
                    bb = s.bit_length() - 1
                    out.append(str(bb * BITS + blk[bb].bit_length() - 1 - OFFSET))
                else:
                    out.append("-1")
        else:                                           # 6 后继：> x 的最小值
            hi = blk[b] >> (r + 1)
            if hi:
                out.append(str(x + 1 + (hi & -hi).bit_length() - 1 - OFFSET))
            else:
                s = summ >> (b + 1)
                if s:
                    bb = b + 1 + (s & -s).bit_length() - 1
                    v = blk[bb]
                    out.append(str(bb * BITS + (v & -v).bit_length() - 1 - OFFSET))
                else:
                    out.append("-1")

    sys.stdout.write("\n".join(out) + "\n")


main()

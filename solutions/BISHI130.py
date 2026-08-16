"""BISHI130 区间取反与区间数一 —— 01 串上的区间翻转 + 区间求 1 的个数。

这题考什么：
    标准解法是「线段树 + 翻转懒标记」（cnt = len - cnt，标记异或）。
    但 n, q <= 5e5、时限「其他语言 4 秒」，Python 下线段树是 5e7 级别的迭代，毫无希望。

    本解法是 **分块 + 大整数位图 + 惰性翻转标记**，把三条路径全部压到 C 层：
      - 每块用一个 B 位的**大整数**当位图（一个 8192 位整数只有 128 个机器字）；
      - 散块翻转 = 一次 `^= mask`；散块计数 = `bin(x).count("1")`——都是 C 层；
      - 整块翻转**不动位图**，只做两件事：
          1. `flipmask ^= 区间掩码`（一次大整数异或，O(nb/64) 机器字，近乎免费）；
          2. `cnt[bl+1:br] = [B - c for c in cnt[bl+1:br]]`（列表推导式，C 层逐元素）；
      - 整块计数 = `sum(cnt[bl+1:br])`（切片 + sum，纯 C 层）；
      - 只有当某块被**散块操作**碰到时，才把它的惰性翻转真正兑现（materialize）。

数据规模与复杂度：
    n, q <= 5e5，块长 B = 4096 时块数 nb ≈ 123。
    每次操作 O(nb) 的 C 层元素操作 + O(B/64) 的机器字操作。

⚠️ Python 现实性判断：**本题在 CPython 3.9 下大概率无法在 4 秒内通过。** 原因是：
    - q = 5e5，每次整块翻转都必须触及 O(nb) 个块的计数（翻转会改变计数，
      无法像「区间加」那样用一个偏移量惰性跳过），列表推导式 123 个元素约 10 μs，
      5e5 次就是 **5 秒**；
    - 散块的 `bin()` 要构造 4096 字符的字符串（约 2 μs），两端 × 5e5 次再加 2 秒；
    - 加大 B 能压低块数，但散块的 `bin()` 成本同比上升，**两头堵死**，
      最优点大致在总耗时 8-10 秒，仍是时限的 2 倍多。
    识别信号：n, q >= 5e5 + 必须区间改区间查 + 信息**不可减** + 时限倍率仅 2。
    这类题的正确做法是承认它、跳过它；本文件保留正确实现作为教学参考（PyPy 下可过）。

坑在哪：
  1. 位图的第 j 位对应块内第 j 个字符，所以建表时要把子串**反过来**再 int(·, 2)；
  2. 中间整块一定不是最后一块，长度必然是 B，所以 `B - c` 是对的；
     只有最后一块可能短，而它只会作为 br（散块）出现；
  3. 惰性标记兑现后一定要把 flipmask 的对应位清掉，否则会翻两次。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); q = int(data[1])
    s = data[2]

    B = 4096
    nb = (n + B - 1) // B
    blk = [0] * nb                           # 每块一个 B 位大整数位图（可能是「未兑现翻转」的）
    cnt = [0] * nb                           # 每块**真实**的 1 的个数
    size = [0] * nb
    fmask = [0] * nb                         # 每块的满位掩码
    for b in range(nb):
        lo = b * B
        hi = min(lo + B, n)
        size[b] = hi - lo
        fmask[b] = (1 << (hi - lo)) - 1
        v = int(s[lo:hi][::-1], 2)           # 第 j 位 = 下标 lo+j 的字符
        blk[b] = v
        cnt[b] = bin(v).count("1")

    flip = 0                                 # 大整数：第 b 位 = 块 b 是否有未兑现的翻转

    p = 3
    out = []
    push = out.append
    for _ in range(q):
        op = data[p]
        l = int(data[p + 1]) - 1
        r = int(data[p + 2]) - 1
        p += 3
        bl = l // B
        br = r // B
        if (flip >> bl) & 1:                 # 兑现左端块的惰性翻转
            blk[bl] ^= fmask[bl]
            flip ^= 1 << bl
        if br != bl and (flip >> br) & 1:    # 兑现右端块
            blk[br] ^= fmask[br]
            flip ^= 1 << br

        if op == b"1":                       # ---- 区间取反 ----
            if bl == br:
                m = ((1 << (r - l + 1)) - 1) << (l - bl * B)
                v = blk[bl] ^ m
                blk[bl] = v
                cnt[bl] = bin(v).count("1")
            else:
                m = fmask[bl] ^ ((1 << (l - bl * B)) - 1)      # 左散块的高位段
                v = blk[bl] ^ m
                blk[bl] = v
                cnt[bl] = bin(v).count("1")
                if br - bl > 1:              # 中间整块：只翻标记 + 更新计数
                    flip ^= ((1 << (br - bl - 1)) - 1) << (bl + 1)
                    cnt[bl + 1:br] = [B - c for c in cnt[bl + 1:br]]
                m = (1 << (r - br * B + 1)) - 1                # 右散块的低位段
                v = blk[br] ^ m
                blk[br] = v
                cnt[br] = bin(v).count("1")
        else:                                # ---- 区间数一 ----
            if bl == br:
                seg = (blk[bl] >> (l - bl * B)) & ((1 << (r - l + 1)) - 1)
                push(bin(seg).count("1"))
            else:
                seg = blk[bl] >> (l - bl * B)
                res = bin(seg).count("1")
                res += sum(cnt[bl + 1:br])                     # ★ C 层求和
                seg = blk[br] & ((1 << (r - br * B + 1)) - 1)
                res += bin(seg).count("1")
                push(res)
    sys.stdout.write("\n".join(map(str, out)) + "\n")


main()

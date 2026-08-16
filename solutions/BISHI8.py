"""BISHI8 大整数哈希 —— 维护 f: [0,2^64) -> [0,2^64)，每次先取旧值再赋新值，
求 sum(i * ans_i) mod 2^64。

这题考什么：
    名字叫「大整数哈希」，本质是「键的值域是 2^64、开不下数组」时怎么做映射。
    C++ 里要手写哈希表（或 unordered_map + 自定义哈希防卡），Python 直接用
    内置 dict 即可：dict 就是哈希表，且大整数的 hash 是 x mod (2^61-1)，
    出题人无法针对 Python 构造哈希攻击数据。
    f(x) 初始为 0 这一点用 dict.get(x, 0) 天然表达，不需要预先填充。

数据规模与复杂度：
    n <= 5e6（本系列最大的一档，输入可达上百 MB），算法本身是 O(n) 的
    哈希表查询 + 赋值，所以**全部时间都花在读入和解释器循环上**，写法必须抠：
      - 不能 sys.stdin.buffer.read().split() 一把梭：那会一次性生成约 1e7 个
        bytes 对象（每个至少 33 字节），光 token 列表就 400MB+，直接 MLE；
        改成每次读 4MB 分块，块内 split 处理完就丢，内存峰值只和 dict 有关；
      - 分块的边界可能把一个数字劈成两半，所以要把「块尾未闭合的 token」
        留到下一块；同理一对 (x, y) 也可能跨块，用 carry 存住落单的那个；
      - 取模只在最后做一次：中间和最多约 2^113，Python 大整数才 2 个 limb，
        每步都 & MASK 反而更慢。

坑在哪：
    1. 输出的是**赋值前**的旧值 ans_i，赋值要放在累加之后；
    2. i 从 1 开始计数，不是从 0；
    3. mod 2^64 是无符号截断，Python 里就是 & ((1<<64)-1)，
       因为过程中全是非负数，不必担心 C 里的有符号溢出 UB；
    4. 旧值为 0（x 第一次出现）时那一项贡献为 0，可以直接跳过累加；
    5. 最坏情况下 dict 会存 5e6 个大整数键值对，内存本身就很吃紧——
       这也是这题在 Python 下真正的难点（值域大到只能靠哈希表，没有别的招）。
"""
import sys

MASK = (1 << 64) - 1
CHUNK = 1 << 22                      # 每次读 4MB


def main() -> None:
    read = sys.stdin.buffer.read
    f = {}
    get = f.get
    total = 0
    idx = 0                          # 已处理的操作序号 i
    n = -1                           # 还没读到 n
    tail = b""                       # 上一块尾部未闭合的半个 token
    carry = None                     # 落单的 x（它的 y 在下一块）

    while True:
        chunk = read(CHUNK)
        if not chunk:
            break
        if tail:
            chunk = tail + chunk
        toks = chunk.split()
        # 块尾若不是空白字符，最后一个 token 可能被截断，留到下一块再拼
        if chunk[-1:].isspace():
            tail = b""
        elif toks:
            tail = toks.pop()
        else:
            tail = b""

        if n < 0:                    # 第一块的第一个 token 是 n
            if not toks:
                continue
            n = int(toks[0])
            toks = toks[1:]

        if carry is not None:        # 接上跨块的那个 x
            toks.insert(0, carry)
            carry = None
        if len(toks) & 1:            # 又落单一个 x，留给下一块
            carry = toks.pop()

        rest = (n - idx) * 2         # 只处理前 n 对，忽略尾部脏数据
        if len(toks) > rest:
            del toks[rest:]

        for j in range(0, len(toks), 2):
            x = int(toks[j])
            idx += 1
            prev = get(x)
            if prev:                 # f(x) 未赋过值时为 0，贡献为 0，跳过
                total += idx * prev
            f[x] = int(toks[j + 1])

        if idx >= n >= 0:
            break

    # 收尾：可能还剩一对 (carry, tail)
    if carry is not None and tail and idx < n:
        idx += 1
        prev = get(int(carry))
        if prev:
            total += idx * prev

    sys.stdout.write(str(total & MASK) + "\n")


main()

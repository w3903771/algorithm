"""BISHI3 【模板】队列操作 —— 入队 / 出队 / 查队首 / 求大小。

这题考什么：
    队列模板。关键是「队头出队」必须 O(1)：list.pop(0) 是 O(n)，
    1e5 次就退化成 O(n^2)。正确写法是数组 + 头指针（本题用），或
    collections.deque。这里用头指针 head 而不是 deque，是因为除了
    出队还要频繁 size（len(a) - head，O(1)），两者等价且更直观。

数据规模与复杂度：
    n <= 1e5，总复杂度 O(n)，空间 O(n)（不回收已出队的槽位，1e5 个
    元素的内存完全够用；若 n 更大可在 head 过大时做一次切片压缩）。

坑在哪：
    1. 操作 2 只有在队列为空时才输出 ERR_CANNOT_POP，正常出队**不输出**；
    2. 操作 3 空队列输出 ERR_CANNOT_QUERY，两个错误串不一样，别复制粘贴串了；
    3. 操作 2/3/4 是单 token，只有操作 1 带参数，用游标解析；
    4. 元素范围到 ±1e9，注意有负数（Python 无所谓，但 split 时不能按
       「非负整数」去做假设）。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    i = 1
    q = []
    head = 0                                 # 队头下标，出队只移动指针，O(1)
    out = []
    for _ in range(n):
        op = data[i]
        i += 1
        if op == b"1":
            q.append(data[i])
            i += 1
        elif op == b"2":
            if head < len(q):
                head += 1
            else:
                out.append("ERR_CANNOT_POP")
        elif op == b"3":
            out.append(q[head].decode() if head < len(q) else "ERR_CANNOT_QUERY")
        else:                                # 4：当前元素个数
            out.append(str(len(q) - head))
    sys.stdout.write("\n".join(out) + "\n")


main()

"""BISHI6 【模板】整数优先队列 —— 插入 / 查询最小值 / 删除最小值。

这题考什么：
    小根堆模板，直接对应 heapq（Python 的 heapq 本来就是小根堆，
    不用像求最大值那样把元素取反再入堆）。
    堆用一个列表存一棵完全二叉树，保证「父节点不大于子节点」，
    于是最小值恒在 h[0]，插入和删除最小值各 O(log n)。
    本题要的三件事恰好就是堆的三个基本操作，一一对应即可：
        插入      -> heappush(h, x)
        查最小值  -> h[0]          （只读，不改动堆）
        删最小值  -> heappop(h)
    见 docs/ds/heap.md。

数据规模与复杂度：
    n <= 1e6（本系列里最大的一档），单次操作 O(log n)，总 O(n log n)。
    这个量级下 **IO 和解释器开销才是瓶颈**，所以：
      - 一次性 sys.stdin.buffer.read().split() 读进所有 token，用整数游标
        往前走，绝不用 1e6 次 input()；
      - 把 heappush / heappop 提前绑成局部变量，省掉 1e6 次属性查找；
      - 输出攒进列表，最后 "\\n".join 一次性 write。

坑在哪：
    1. 操作 2/3 只有一个 token，操作 1 有两个，行长度不固定，必须用游标
       按 token 读而不是按「每行两个数」读；
    2. 操作 2 是**查询**最小值（不删除），操作 3 是**删除**最小值（不输出），
       两者不能混；只有操作 2 产生输出；
    3. 查询最小值直接看 h[0] 就行，不要 heappop 之后再 heappush（多两次
       O(log n) 调整，白白慢一倍）；
    4. 题面没说操作 2/3 会在空集合上出现，但判空只多一次比较，
       写上就不会因为 h[0] 越界而 RE（运行时错误）；
    5. 输出时把 int 攒进 out、最后统一 map(str, out)，比每次 append(str(x))
       少 1e6 次 Python 层的函数调用；join 之前只做一次转换即可。

样例复核：
    依次 push 5、3 后堆顶是 3，第一次查询输出 3；push 10 不改变最小值，
    第二次查询仍输出 3；操作 3 弹出 3，堆里剩 5 和 10，最后一次查询输出 5。
    与样例一致。
"""
import sys
from heapq import heappush, heappop


def main() -> None:
    # n 可达 1e6，IO 和解释器开销才是瓶颈：一次性读进所有 token，
    # 用整数游标往前走，绝不做 1e6 次 input()
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    i = 1                                # data[0] 是操作条数，操作从下标 1 开始
    h = []                               # heapq 维护的小根堆，最小值恒在 h[0]
    out = []                             # 先攒 int，join 之前再统一转字符串
    push, pop = heappush, heappop        # 绑成局部名，1e6 次调用能省下可观开销
    for _ in range(n):
        op = data[i]
        i += 1
        if op == b"1":
            push(h, int(data[i]))
            i += 1
        elif op == b"2":                 # 查询最小值，不删
            # 直接读 h[0] 即可；pop 完再 push 会白白多两次 O(log n) 的调整
            if h:
                out.append(h[0])
        else:                            # 3：删除一个最小值，不输出
            # 题面没保证操作 2/3 不会落在空堆上，判空只多一次比较，写上就不会 RE
            if h:
                pop(h)
    # map(str, out) 只在这里做一次转换，省下 1e6 次 append(str(x)) 的调用
    sys.stdout.write("\n".join(map(str, out)) + "\n")


main()

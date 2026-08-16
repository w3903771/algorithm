"""BISHI6 【模板】整数优先队列 —— 插入 / 查询最小值 / 删除最小值。

这题考什么：
    小根堆模板，直接对应 heapq（Python 的 heapq 本来就是小根堆，
    不用像求最大值那样取反）。

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
    4. 空集合时的 2/3 题面没说会出现，但加个判空更稳，免得 RE。
"""
import sys
from heapq import heappush, heappop


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    i = 1
    h = []
    out = []
    push, pop = heappush, heappop        # 绑成局部名，1e6 次调用能省下可观开销
    for _ in range(n):
        op = data[i]
        i += 1
        if op == b"1":
            push(h, int(data[i]))
            i += 1
        elif op == b"2":                 # 查询最小值，不删
            if h:
                out.append(h[0])
        else:                            # 3：删除一个最小值，不输出
            if h:
                pop(h)
    sys.stdout.write("\n".join(map(str, out)) + "\n")


main()

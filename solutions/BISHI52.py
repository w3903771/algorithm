"""BISHI52 奥赛组队 —— 选 p 人进编程队、s 人进体育队（不重叠），最大化 a 和 + b 和。

这题考什么：
    交换论证 + 前后缀「前 k 大之和」。

    关键引理：设最优解里 i 进编程队、j 进体育队，若 a_i - b_i < a_j - b_j，
    把两人对调，总实力变化 (a_j + b_i) - (a_i + b_j) = (a_j-b_j)-(a_i-b_i) > 0，
    与最优矛盾。所以最优解中「编程队每个人的 a-b」都 >= 「体育队每个人的 a-b」。

    于是把所有人按 a_i - b_i **降序**排好（并列时可任意排，总能把编程队的人
    排在前面），则一定存在分界点 t，使编程队全在前 t 个、体育队全在后 n-t 个。
    枚举 t（p <= t <= n-s）：
        答案 = (前 t 个里 a 最大的 p 个之和) + (后 n-t 个里 b 最大的 s 个之和)
    前者随 t 递增可用「大小为 p 的小根堆」在线维护，后者倒着扫一遍同理。

数据规模与复杂度：
    n <= 3000。O(n^2) 也能过，但堆做法只要 O(n log n)，而且代码更短。
    需要输出方案，所以确定最优 t 后再单独排一次序把编号取出来。

坑在哪：
  1. 排序键写 a-b 降序（等价于 b-a 升序），写反了直接错；
  2. p 或 s 可能为 0（题目只保证 p+s <= n），堆维护里要挡住 p==0/s==0，
     此时该行输出空行；
  3. 答案不唯一（并列能力值随便挑一个都行），本题配了 solutions/_spj/BISHI52.py
     校验：验证编号合法/不重复/两队不相交、三行自洽，且总和等于最优值；
  4. 输出的是**输入次序**的编号（1..n），排序后别忘了带着原下标。
"""
import heapq
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n, p, s = int(data[0]), int(data[1]), int(data[2])
    a = [int(x) for x in data[3:3 + n]]
    b = [int(x) for x in data[3 + n:3 + 2 * n]]

    # 按 a-b 降序 == 按 b-a 升序
    order = sorted(range(n), key=lambda i: b[i] - a[i])

    # f[t] = order[:t] 中 a 最大的 p 个之和
    f = [0] * (n + 1)
    h = []
    cur = 0
    for t in range(1, n + 1):
        v = a[order[t - 1]]
        if len(h) < p:
            heapq.heappush(h, v)
            cur += v
        elif p and v > h[0]:
            cur += v - heapq.heapreplace(h, v)
        f[t] = cur

    # g[t] = order[t:] 中 b 最大的 s 个之和
    g = [0] * (n + 1)
    h = []
    cur = 0
    for t in range(n - 1, -1, -1):
        v = b[order[t]]
        if len(h) < s:
            heapq.heappush(h, v)
            cur += v
        elif s and v > h[0]:
            cur += v - heapq.heapreplace(h, v)
        g[t] = cur

    best, bt = -1, p
    for t in range(p, n - s + 1):
        if f[t] + g[t] > best:
            best, bt = f[t] + g[t], t

    # 还原方案：前缀里取 a 最大的 p 个，后缀里取 b 最大的 s 个
    head = sorted(order[:bt], key=lambda i: -a[i])[:p]
    tail = sorted(order[bt:], key=lambda i: -b[i])[:s]
    out = [str(best),
           " ".join(str(i + 1) for i in head),
           " ".join(str(i + 1) for i in tail)]
    sys.stdout.write("\n".join(out) + "\n")


main()

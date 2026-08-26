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

答案为什么不唯一：
    题面只要求「总实力最大」，最大值本身唯一，但达到它的**名单**通常有很多份，
    并列来自三个互相独立的地方：
      1. a_i - b_i 相同的人在排序里谁先谁后无所谓，交换他们不改变任何一个
         分界点的取值；
      2. 前缀里 a 值相同的人挑谁都一样（后缀里 b 值相同同理）——
         比如两人 a 都是 5 而只招 1 个，招谁总和都不变；
      3. 分界点 t 本身可能有多个取到同一个最大值：位于分界线附近、
         既没进编程队也没进体育队的「闲人」，往左往右挪都不影响两队的选人。
    所以本题用**特判**（SPJ，Special Judge，即由一段校验程序判定选手输出
    是否合法，而不是与标准答案逐字符比对）来评测。
    校验器在 spj.py：它独立算一遍最优值 opt，
    再检查第一行等于 opt、第二/三行是 p 个与 s 个互不相同且互不相交的
    合法编号（1..n），并且这两队的实际实力之和确实等于第一行报出的数。
    四项全过才算 AC。

本解法选了哪种构造：
    本解法的输出是确定的（不依赖任何随机顺序），定死名单的规则有三条：
      - 排序用 sorted(..., key=lambda i: b[i] - a[i])。Python 的 sort 稳定，
        所以 a-b 并列时按输入编号从小到大排；
      - 枚举分界点时用严格的 `>` 更新最优，因此取到的是**最小的可行 t**，
        也就是编程队的候选前缀尽可能短；
      - 还原名单时对前缀按 -a[i] 排序取前 p 个、对后缀按 -b[i] 取前 s 个，
        同样借助稳定排序，在能力值并列时优先选 order 里靠前的人。
    样例 1 用这套规则得到的名单是「编程队 4 3 / 体育队 1 5」，
    与题面示例的「3 4 / 1 5」只差队内顺序 —— 队内顺序题目不作要求，
    校验器也只看集合，两者都对。

坑在哪：
  1. 排序键写 a-b 降序（等价于 b-a 升序），写反了直接错；
  2. p 或 s 可能为 0（题目只保证 p+s <= n），堆维护里要挡住 p==0/s==0，
     否则 `v > h[0]` 会访问空堆；此时对应那一行输出空行，不能省略，
     校验器按「第 2 行是编程队、第 3 行是体育队」定位，少一行就对不上；
  3. 输出的是**输入次序**的编号（1..n），排序后别忘了带着原下标；
  4. 分界点的枚举范围是 p <= t <= n-s：左端保证前缀够 p 个人，
     右端保证后缀够 s 个人，写宽了会读到没填满的 f/g。

    贪心与交换论证见 docs/basic/greedy.md，
    堆的用法见 docs/ds/heap.md。
"""
import heapq
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n, p, s = int(data[0]), int(data[1]), int(data[2])
    a = [int(x) for x in data[3:3 + n]]
    b = [int(x) for x in data[3 + n:3 + 2 * n]]

    # 按 a-b 降序 == 按 b-a 升序；排序稳定，并列时保持输入编号从小到大
    order = sorted(range(n), key=lambda i: b[i] - a[i])

    # f[t] = order[:t] 中 a 最大的 p 个之和；从左往右扫，用大小为 p 的小根堆维护
    f = [0] * (n + 1)
    h = []
    cur = 0                            # 堆内元素之和，避免每步重新 sum
    for t in range(1, n + 1):
        v = a[order[t - 1]]
        if len(h) < p:                 # 还没招满，直接收下
            heapq.heappush(h, v)
            cur += v
        elif p and v > h[0]:           # 招满了才考虑替换；p==0 时短路，防止读空堆
            cur += v - heapq.heapreplace(h, v)   # 换掉堆顶（当前最小的那个 a）
        f[t] = cur

    # g[t] = order[t:] 中 b 最大的 s 个之和；对称地倒着扫一遍
    g = [0] * (n + 1)
    h = []
    cur = 0
    for t in range(n - 1, -1, -1):
        v = b[order[t]]
        if len(h) < s:
            heapq.heappush(h, v)
            cur += v
        elif s and v > h[0]:           # 同上，s==0 时短路
            cur += v - heapq.heapreplace(h, v)
        g[t] = cur

    # 枚举分界点：前缀至少要有 p 人、后缀至少要有 s 人，故 t 取 [p, n-s]
    best, bt = -1, p
    for t in range(p, n - s + 1):
        if f[t] + g[t] > best:         # 严格大于 -> 并列时保留更小的 t
            best, bt = f[t] + g[t], t

    # 还原方案：前缀里取 a 最大的 p 个，后缀里取 b 最大的 s 个
    head = sorted(order[:bt], key=lambda i: -a[i])[:p]
    tail = sorted(order[bt:], key=lambda i: -b[i])[:s]
    # 下标转回题面的 1 基编号；p 或 s 为 0 时对应行是空串，仍要占一行
    out = [str(best),
           " ".join(str(i + 1) for i in head),
           " ".join(str(i + 1) for i in tail)]
    sys.stdout.write("\n".join(out) + "\n")


main()

"""BISHI95 【模板】链式前向星 —— 无向图，按升序输出每个点的全部邻居。

这题考什么：
    图的存储方式模板。C++ 里链式前向星是「head[u] + nxt[] + to[] 三个数组
    模拟链表」，本质就是一个**紧凑的邻接表**（CSR）。
    本题在存完之后还要求把每个点的邻居**升序**输出，所以存完还得排序。

Python 的实现选择（重点）：
  1. 邻接表**不要用 defaultdict(list)**：1e5 个点时字典的哈希开销、
     以及 list 的按需扩容都会明显拖慢，而且顺序不确定；
  2. 这里直接开 `adj = [[] for _ in range(n+1)]` 的定长 list of list，
     下标即点号，append 是 O(1) 均摊；
     （也可以照搬链式前向星的三数组写法，但在 Python 里遍历链表指针
       反而比遍历 list 慢，list of list 才是等价且更快的实现。）
  3. 每个点的邻居单独 sort，总代价 Σ deg(u) log deg(u) <= O(m log m)。

数据规模与复杂度：
    n, m <= 1e5 -> 无向边共 2e5 个方向。建表 O(n + m)，排序 O(m log m)，
    输出 O(n + m)。

Python 的坑：
  1. 输出有 n 行、总计 2e5 个数字，必须先拼成一个大字符串再一次 write；
     逐行 print 在 1e5 行时会明显变慢；
  2. 孤立点要输出 "None"（首字母大写），别输出空行；
  3. 题面没有说「不存在重边 / 自环」。链式前向星的本义是**如实存下每条边**，
     所以这里**不做去重**：给了两条 1-2 就输出两个 2；
     若出现自环 a==b，按无向图的存法会在 a 的邻居里出现两次 a——
     这与「照抄边表」的模板语义一致。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n, m = int(data[0]), int(data[1])
    adj = [[] for _ in range(n + 1)]     # 定长 list of list，不用 defaultdict

    p = 2
    for _ in range(m):
        a = int(data[p]); b = int(data[p + 1]); p += 2
        adj[a].append(b)
        adj[b].append(a)

    out = []
    for u in range(1, n + 1):
        e = adj[u]
        if e:
            e.sort()
            out.append(" ".join(map(str, e)))
        else:
            out.append("None")
    sys.stdout.write("\n".join(out) + "\n")


main()

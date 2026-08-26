"""BISHI99 我朋友的朋友不是我的朋友 —— 找出所有满足 deg(x) > 平均邻居度数 的点。

这题考什么：
    图的度数统计 + 一次「避免浮点」的不等式变形。
        deg(x) > avg(x) = (Σ_{y∈N(x)} deg(y)) / deg(x)
    两边同乘 deg(x)（deg(x) > 0，不改变方向）得到
        deg(x)^2 > Σ_{y∈N(x)} deg(y)
    全部是整数比较，**彻底绕开浮点精度**（用 float 比较在 deg 大时会出错）。

数据规模与复杂度：
    n, m <= 1e5。两遍扫边：第一遍统计每个人的度数，第二遍把每条边的两端
    互相累加对方的度数。复杂度 O(m + n log n)（末尾排序）。

Python 的坑：
  1. 点是**字符串**而不是编号，所以必须先把名字映射成整数 id
     （用一个 dict 做 name -> id），之后所有统计都在数组上做——
     直接拿字符串当 dict 的 key 反复读写会慢好几倍；
  2. 名字全是小写字母，**保持 bytes 不 decode 直接排序**，
     字节序就是字典序，最后输出时才 decode；
  3. 一次 read + split，m 行每行两个 token，按游标取。

坑在哪：
  1. 题面给了 n（成员总数），但只有出现在边里的人才知道名字。
     度数为 0 的人 avg 是 0/0 无定义，自然不可能是社牛，直接忽略；
  2. 保证无重边、无自环，所以 deg 就是不同好友数，不用去重；
  3. 没有社牛时要输出 "None"（首字母大写），不是空行。

样例复核：
    三角形，每人 deg = 2，邻居度数和 = 4，判定 2^2 = 4 > 4 不成立 -> None ✓
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    m = int(data[1])                    # n 不必读：没出现在边里的人度数为 0，不可能是社牛

    # ---- 把名字映射成 0..k-1 的整数 id，后续统计全在数组上做 ----
    idx = {}                            # 名字 -> id
    names = []                          # names[id] = 原始 bytes 名字
    edges = []
    p = 2
    for _ in range(m):
        a = data[p]; b = data[p + 1]; p += 2
        ia = idx.get(a, -1)
        if ia < 0:                      # 第一次见到这个名字，分配一个新 id
            ia = len(names); idx[a] = ia; names.append(a)
        ib = idx.get(b, -1)
        if ib < 0:
            ib = len(names); idx[b] = ib; names.append(b)
        edges.append((ia, ib))

    # ---- 第一遍扫边：统计每个人的度数 ----
    k = len(names)
    deg = [0] * k
    for ia, ib in edges:
        deg[ia] += 1
        deg[ib] += 1

    # ---- 第二遍扫边：度数已经全部就绪，两端互相累加对方的度数 ----
    nbr = [0] * k                       # nbr[x] = 邻居度数之和
    for ia, ib in edges:
        nbr[ia] += deg[ib]
        nbr[ib] += deg[ia]

    # deg(x) > avg(x)  <=>  deg(x)^2 > Σ deg(邻居)，全整数比较
    res = [names[i] for i in range(k) if deg[i] * deg[i] > nbr[i]]
    if not res:
        sys.stdout.write("None\n")
        return
    res.sort()                          # bytes 排序 == 小写字母的字典序
    sys.stdout.write(b" ".join(res).decode() + "\n")   # 拼完整行再 decode，只转一次


main()

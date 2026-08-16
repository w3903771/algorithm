"""BISHI136 【模板】01背包 —— 同时求「不要求装满」和「恰好装满」两问。

这题考什么：
    01 背包的一维滚动数组写法，以及**「恰好装满」与「不要求装满」只差在初值**这一经典对比。

        f[c] = max(f[c], f[c - v] + w)     容量倒序遍历
      - 不要求装满：f 全初始化为 0（任何容量都合法，初始价值 0）；
      - 恰好装满：  f[0] = 0，其余初始化为 **-∞**（表示「凑不出这个体积」）。

    **为什么必须倒序**：f[c-v] 必须还是「上一轮（不含本物品）」的值，
    正序会让同一件物品被重复选（那是完全背包）。

数据规模与复杂度：
    n, V <= 1e3，O(nV) = 1e6，O(V) 空间——正好是题目备注要求的复杂度。

Python 关键：
    **把内层的容量循环下沉到 C 层**。一维倒序循环
        for c in range(V, v-1, -1): f[c] = max(f[c], f[c-v]+w)
    等价于一次「整段取 max」：
        f[v:] = list(map(max, f[v:], [x + w for x in f[:V+1-v]]))
    右边的候选数组是**在赋值之前**用旧的 f 算好的，所以 01 语义自动成立，
    而且列表推导式 + map 全在 C 层，比 1e6 次 Python 迭代快 5-8 倍。

坑在哪：
  1. 「恰好装满」无解时输出 0（不是 -1、不是负数）；
  2. -∞ 不能取 -1 这种「小负数」——加上 w 之后可能变成正数把答案带歪。
     这里取 -1e18，加满 1e3 个 1e3 也只是 -1e18+1e6，仍然远小于 0；
  3. v_i >= 1，不用担心体积为 0 的自环。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); V = int(data[1])
    NEG = -(1 << 60)                         # 「凑不出」的哨兵，加法后仍远小于 0
    f1 = [0] * (V + 1)                       # 不要求装满
    f2 = [NEG] * (V + 1)                     # 恰好装满
    f2[0] = 0
    p = 2
    for _ in range(n):
        v = int(data[p]); w = int(data[p + 1])
        p += 2
        if v > V:
            continue
        m = V + 1 - v
        f1[v:] = list(map(max, f1[v:], [x + w for x in f1[:m]]))
        f2[v:] = list(map(max, f2[v:], [x + w for x in f2[:m]]))
    sys.stdout.write("%d\n%d\n" % (f1[V], f2[V] if f2[V] >= 0 else 0))


main()

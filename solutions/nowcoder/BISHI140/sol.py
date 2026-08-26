"""BISHI140 【模板】分组背包 —— 同一组内至多选一件。

这题考什么：
    分组背包的循环顺序，这是最容易写错的地方：
        for 每一组:
            for 容量 c 倒序:
                for 组内每件物品 i:
                    f[c] = max(f[c], f[c - w_i] + v_i)
    **「组」在最外层、「物品」在最内层**。含义是：处理完一组后 f 才更新一次，
    所以组内所有物品的候选都来自「上一组结束时」的 f，天然保证至多选一件。
    写成「物品在外、容量在内」就退化成普通 01 背包（一组能选多件）。

Python 关键：
    把上面的三重循环改写成「每组一个临时数组 tmp」：
        tmp = f[:]                              # 这一组什么都不选
        for (w, v) in 组内物品:
            cand = [x + v for x in f[:M+1-w]]   # ★ 候选一律来自旧的 f
            tmp[w:] = list(map(max, tmp[w:], cand))
        f = tmp
    候选取自 f（旧的）而不是 tmp（本组已经选过的），组内互斥就成立了；
    同时内层全是 C 层的 map / 列表推导，Python 层循环只有 n 次。

数据规模与复杂度：
    n, M <= 2000，总共 O(nM) = 4e6 次 C 层元素操作，不到 0.5 秒。

坑在哪：
  1. **w_i 最大 1e9**，远超 M = 2000，这类物品要直接跳过，
     否则切片 f[:M+1-w] 会因为负数下标算出空列表甚至错位；
  2. 组号 g_i <= 100，但不保证连续/从 1 开始出现，用字典分组最稳；
  3. v_i 最大 1e9，答案最大 2000 × 1e9 = 2e12，C++ 要 long long；
  4. 「至多选一件」不是「必须选一件」，所以 tmp 的初值是 f 的拷贝。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); M = int(data[1])
    # 组号不保证连续、也不保证从 1 开始，用字典按组归拢；
    # 键直接用未转 int 的 bytes，反正只当标识用，省 n 次转换
    groups = {}
    p = 2
    for _ in range(n):
        w = int(data[p]); v = int(data[p + 1]); g = data[p + 2]
        p += 3
        if w > M:                            # w 可到 1e9，装不下的直接丢
            continue                         # 留着会让下面的 M + 1 - w 变成负数，切片错位
        groups.setdefault(g, []).append((w, v))

    f = [0] * (M + 1)                        # 至多选一件而非必须选，初值全 0
    for items in groups.values():
        tmp = f[:]                           # 本组「一件都不选」
        for w, v in items:
            # 组内每件物品的候选都取自本组开始前的 f，彼此看不见对方，
            # 于是「一组至多选一件」自动成立；结果累积在 tmp 上
            cand = [x + v for x in f[:M + 1 - w]]    # ★ 候选来自旧的 f
            tmp[w:] = list(map(max, tmp[w:], cand))
        f = tmp                              # 整组处理完才更新 f，等价于「组在最外层」
    sys.stdout.write("%d\n" % f[M])


main()

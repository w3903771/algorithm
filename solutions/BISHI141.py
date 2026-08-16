"""BISHI141 来硬的 —— 选若干煤炭烧完 m 单位矿石，至多对一枚施魔法，求最短总时间。

这题考什么：
    「**至少覆盖 m**」型的 01 背包（把容量维当成「已融化的矿石量」，
    超过 m 的部分一律并到 m 这一格），外加一维 0/1 状态表示魔法是否用过。

        f0[j] = 融化至少 j 单位、**没用**魔法的最短时间
        f1[j] = 融化至少 j 单位、**用过**魔法的最短时间
        对每枚煤炭 (x, y)：
            f0[j] <- min(f0[j], f0[j-x] + y)                 不升级
            f1[j] <- min(f1[j], f1[j-x] + y,                 不升级（此前已用过魔法）
                               f0[j-2x] + y//2)              把魔法用在这一枚
        其中 j-x 一律用 max(0, j-x)——这就是「至少」的实现方式：
        剩余需求不会变成负数，多融化的部分不额外记账。
    答案 = min(f0[m], f1[m])。

数据规模与复杂度：
    保证 **n·m <= 1e6**（这是本题唯一的规模约束，n 或 m 单独可以很大），
    所以 O(nm) 的状态转移总量不超过 3e6 次 C 层元素操作。

Python 关键：
    每一步的「平移 + 加常数 + 取 min」写成一次批处理：
        shift(d, cap, cost)[j] = d[max(0, j-cap)] + cost
        实现为 [d[0]+cost]*cap + [x+cost for x in d[:m+1-cap]]
    然后 `list(map(min, 旧数组, 平移数组))`。全程 C 层。
    注意 f1 的三个来源要**先全部用旧值算好**再一起赋值，
    否则 f0 被本轮更新后再拿去算 f1 就重复用了同一枚煤炭。

坑在哪：
  1. **y 保证是偶数**，所以 y//2 是精确的，不用担心取整；
  2. 升级后是「时间减半、矿石翻倍」，两个属性都要变，只改一个是常见错误；
  3. 魔法「至多」施放一次，也可以不施——所以答案要对 f0[m] 和 f1[m] 取 min；
  4. 2x 可能超过 m，平移函数要能处理 cap > m 的情形；
  5. 数据保证 Σx_i >= m，一定有解，但 INF 哨兵还是要够大（这里用 1<<60）。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); m = int(data[1])
    INF = 1 << 60
    f0 = [0] + [INF] * m                     # 没用魔法
    f1 = [INF] * (m + 1)                     # 用过魔法

    def shift(d, cap, cost):
        """返回 t，其中 t[j] = d[max(0, j-cap)] + cost。"""
        if cap >= m:
            return [d[0] + cost] * (m + 1)
        head = d[0] + cost
        return [head] * cap + [x + cost for x in d[:m + 1 - cap]]

    p = 2
    for _ in range(n):
        x = int(data[p]); y = int(data[p + 1])
        p += 2
        a0 = shift(f0, x, y)                 # 普通使用
        a1 = shift(f1, x, y)                 # 普通使用（魔法此前已用掉）
        a2 = shift(f0, 2 * x, y >> 1)        # ★ 把唯一一次魔法用在这一枚
        f1 = list(map(min, f1, a1, a2))
        f0 = list(map(min, f0, a0))
    ans = f0[m]
    if f1[m] < ans:
        ans = f1[m]
    sys.stdout.write("%d\n" % ans)


main()

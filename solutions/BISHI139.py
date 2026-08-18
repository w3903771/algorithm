"""BISHI139 【模板】二维费用背包 —— 时间 T、精力 H 两个限制，求最大快乐值。

这题考什么：
    二维费用背包：状态多一维，转移形式不变。
        f[t][h] = max(f[t][h], f[t - t_i][h - h_i] + a_i)
    **两维都要倒序遍历**（01 背包语义），或者等价地：外层 t 倒序，
    内层用「整段取 max」时保证候选取自 f[t - t_i]（本轮还没被改过的那一行）。

数据规模与复杂度：
    n <= 50，T, H <= 500，状态数 50 × 501 × 501 ≈ 1.25e7。
    纯 Python 三重循环是 1.25e7 次迭代（约 10 秒），必须把最内层下沉到 C 层。

Python 关键：
    把 f 存成「每个 t 一行、行内是 h 维」的二维列表，内层整行批处理：
        cand = [x + a for x in f[t - ti][:H + 1 - hi]]
        f[t][hi:] = list(map(max, f[t][hi:], cand))
    这样 Python 层只剩 n × T = 2.5e4 次循环，内层 1.25e7 次元素操作全在 C 层，
    实测 1 秒出头。

坑在哪：
  1. **外层 t 必须倒序**：正序会让 f[t-ti] 已经含有本物品，变成完全背包；
  2. 倒序时 f[t - ti] 因为 t-ti < t 且我们从大到小改，所以还是旧值——正确；
  3. a_i 最大 1e9、n = 50，总和到 5e10，C++ 要 long long；
  4. 无解（任何单个事件都超限）时答案是 0，f 初值全 0 天然覆盖，不需要 -∞；
  5. t_i, h_i >= 1，不存在零费用自环。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    T = int(data[1]); H = int(data[2])
    # f[t][h] = 用时不超过 t、精力不超过 h 时的最大快乐值。
    # 全 0 初值同时表达了「什么都不选也合法」，所以无解时自然输出 0
    f = [[0] * (H + 1) for _ in range(T + 1)]
    p = 3
    for _ in range(n):
        ti = int(data[p]); hi = int(data[p + 1]); a = int(data[p + 2])
        p += 3
        if ti > T or hi > H:                 # 单个事件就超限，永远选不了
            continue
        lim = H + 1 - hi                     # 候选段长度：源精力 0..H-hi 对应目标 hi..H
        for t in range(T, ti - 1, -1):       # ★ 时间维倒序 -> 每个事件只用一次
            src = f[t - ti]                  # t - ti < t，倒序下这一行本轮还没被改过
            row = f[t]
            # 精力维不必再写循环：整行一次 map(max)，1.25e7 次元素比较全落在 C 层
            row[hi:] = list(map(max, row[hi:], [x + a for x in src[:lim]]))
    sys.stdout.write("%d\n" % f[T][H])       # 两维都是「不超过」，右下角即全局最优


main()

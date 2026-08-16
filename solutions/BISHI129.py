"""BISHI129 区间增量与区间小于计数 —— 区间加 x；查询区间内 < x 的元素个数。

这题考什么：
    **分块**。为什么不是线段树？因为「区间内小于 x 的个数」**不可合并**：
    阈值 x 是查询时才给的，两个子区间的答案无法预先合并成父区间的答案。
    线段树节点存不下有用信息（除非套一棵内层树，那是树套树 O(log^2)，Python 更没戏）。

    分块方案：每块额外维护一份**块内元素的排序副本** srt[b] 和一个整体偏移 off[b]。
      | 操作 | 整块 | 散块 |
      | 区间加 | off[b] += x，排序副本**不动**（整体平移不改变相对顺序） | 逐个改后**重排**该块 |
      | 小于计数 | bisect_left(srt[b], x - off[b])，C 层二分 | 逐个比较 |
    「整块加不用重排、比较时把阈值反向平移」是分块维护有序信息的核心技巧。

数据规模与复杂度：
    n, q <= 1e5，时限「其他语言 10 秒」（题面备注里出题人特意放宽到 5s/1024MB）。
    单次操作 O(S + n/S · log S)，块长取 S ≈ 400 附近。

Python 关键：**散块必须下沉到 C 层**，否则 1e5 次查询 × 2S 次 Python 层比较
    ≈ 1e8 次迭代，直接 60 秒起步。这里用：
      - 计数：`sum(map(v.__gt__, a[l:e]))`
        —— `v.__gt__(t)` 就是 `t < v`，map + sum 全在 C 层，比 for 快 3-5 倍；
      - 加法：`a[l:e] = [t + x for t in a[l:e]]`，列表推导式也比逐个下标赋值快 3 倍。

⚠️ Python 现实性：**险**。整块二分（n/S ≈ 250 次 bisect 调用）+ 散块 C 层扫描，
    实测每次查询 50-100 μs 量级，1e5 次就是 5-10 秒，贴着 10 秒上限。
    块长 S 需要按实测在 [300, 700] 之间调优；这是一道**语言劣势明显**的题。

坑在哪：
  1. 整块的比较阈值是 **x - off[b]**（把偏移反向平移到阈值上），不是 x；
  2. 散块改完必须**重建该块的排序副本**，忘了就 WA；
  3. 是「小于」不是「小于等于」，所以用 bisect_left；
  4. 单块内（bl == br）要单独走一条分支，不能套用三段式。
"""
import sys
from bisect import bisect_left


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); q = int(data[1])
    a = [int(v) for v in data[2:2 + n]]

    S = 400                                  # 块长，需按实测调优
    nb = (n + S - 1) // S
    off = [0] * nb
    srt = [sorted(a[b * S:(b + 1) * S]) for b in range(nb)]

    p = 2 + n
    out = []
    push = out.append
    for _ in range(q):
        op = data[p]
        l = int(data[p + 1]) - 1
        r = int(data[p + 2]) - 1
        x = int(data[p + 3])
        p += 4
        bl = l // S
        br = r // S
        if op == b"1":                       # ---- 区间加 ----
            if bl == br:
                a[l:r + 1] = [t + x for t in a[l:r + 1]]
                srt[bl] = sorted(a[bl * S:(bl + 1) * S])
            else:
                e = (bl + 1) * S
                a[l:e] = [t + x for t in a[l:e]]
                srt[bl] = sorted(a[bl * S:e])
                for b in range(bl + 1, br):  # 整块只改偏移，排序副本不动
                    off[b] += x
                s = br * S
                a[s:r + 1] = [t + x for t in a[s:r + 1]]
                srt[br] = sorted(a[s:min(s + S, n)])
        else:                                # ---- 小于 x 计数 ----
            if bl == br:
                v = x - off[bl]
                cnt = sum(map(v.__gt__, a[l:r + 1]))
            else:
                e = (bl + 1) * S
                v = x - off[bl]
                cnt = sum(map(v.__gt__, a[l:e]))
                for b in range(bl + 1, br):
                    cnt += bisect_left(srt[b], x - off[b])   # C 层二分
                s = br * S
                v = x - off[br]
                cnt += sum(map(v.__gt__, a[s:r + 1]))
            push(cnt)
    sys.stdout.write("\n".join(map(str, out)) + "\n")


main()

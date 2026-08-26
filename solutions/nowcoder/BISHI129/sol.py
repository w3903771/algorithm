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

常数分析：
    整块二分（每次约 n/S ≈ 250 回 bisect 调用）加两端散块的 C 层扫描，
    每次查询在 50-100 μs 量级，1e5 次查询合计数秒；时限 10 秒能过，但余量不大。
    块长 S 在 [300, 700] 之间都可行，取 400 是较稳的一档。

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
    a = [int(v) for v in data[2:2 + n]]      # 存的是「不含块偏移」的裸值，0 下标

    # 每块维护两样东西：整体偏移 off[b]，以及块内裸值的排序副本 srt[b]。
    # 下标 i 的真实值始终等于 a[i] + off[i // S]
    S = 400                                  # 块长，需按实测调优
    nb = (n + S - 1) // S
    off = [0] * nb
    srt = [sorted(a[b * S:(b + 1) * S]) for b in range(nb)]   # 末块不满，切片自动截断

    p = 2 + n                                # 操作段在 data 里的起始位置
    out = []
    push = out.append                        # 绑成局部名，省掉循环里的属性查找
    for _ in range(q):
        op = data[p]                         # 保持 bytes 原样比较，省一次 int() 转换
        l = int(data[p + 1]) - 1             # 题面下标从 1 起，统一减 1 转成 0 下标
        r = int(data[p + 2]) - 1
        x = int(data[p + 3])
        p += 4
        bl = l // S                          # 左端点所在块
        br = r // S                          # 右端点所在块
        if op == b"1":                       # ---- 区间加 ----
            if bl == br:                     # 整段落在同一块里，只动这一块
                # 切片整体替换比逐个下标赋值快得多，列表推导跑在 C 层
                a[l:r + 1] = [t + x for t in a[l:r + 1]]
                srt[bl] = sorted(a[bl * S:(bl + 1) * S])     # 散块改过，排序副本必须重建
            else:
                e = (bl + 1) * S             # 左端所在块的末尾（开区间）
                a[l:e] = [t + x for t in a[l:e]]
                srt[bl] = sorted(a[bl * S:e])
                for b in range(bl + 1, br):  # 整块只改偏移，排序副本不动
                    off[b] += x              # 整体平移不改变块内相对顺序，故无需重排
                s = br * S                   # 右端所在块的开头
                a[s:r + 1] = [t + x for t in a[s:r + 1]]
                srt[br] = sorted(a[s:min(s + S, n)])         # 末块可能不满，用 min 收住
        else:                                # ---- 小于 x 计数 ----
            if bl == br:
                # v.__gt__(t) 就是 t < v，map + sum 全程在 C 层跑，
                # 比写 Python 的 for 循环逐个比较快 3-5 倍
                v = x - off[bl]              # 把块偏移反向平移到阈值上
                cnt = sum(map(v.__gt__, a[l:r + 1]))
            else:
                e = (bl + 1) * S
                v = x - off[bl]
                cnt = sum(map(v.__gt__, a[l:e]))             # 左散块逐个比较
                for b in range(bl + 1, br):
                    # 整块有序，直接二分。问「小于」而非「小于等于」，所以是 bisect_left
                    cnt += bisect_left(srt[b], x - off[b])   # C 层二分
                s = br * S
                v = x - off[br]
                cnt += sum(map(v.__gt__, a[s:r + 1]))        # 右散块逐个比较
            push(cnt)
    sys.stdout.write("\n".join(map(str, out)) + "\n")


main()

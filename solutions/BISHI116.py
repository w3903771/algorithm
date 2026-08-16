"""BISHI116 【模板】双指针 —— 找出所有「元素两两不同」的最长区间。

这题考什么：
    最经典的「无重复字符最长子串」双指针，外加一步「把所有最长区间都列出来」。

    维护 last[v] = 值 v 最近一次出现的下标。右端点 r 从左往右扫，
    左端点 l 只会**单调右移**：当 a[r] 在 [l, r-1] 中出现过时，
    直接把 l 跳到 last[a[r]] + 1。每个下标各被 l、r 扫过一次，O(n)。

    第二步的关键结论：**对每个 r，以 r 结尾的合法区间里最长的那个是唯一的**，
    即 [lo(r), r]。若某个长度为 best 的合法区间 [l, r] 存在，
    则必有 lo(r) <= l 且 r - lo(r) + 1 <= best，两边一夹得 l = lo(r)。
    所以「所有最长区间」= {(lo(r), r) : r - lo(r) + 1 == best}，每个 r 至多贡献一个。

数据规模与复杂度：
    n <= 2e5，O(n) 时间、O(n) 空间（a_i <= n，用数组当哈希表）。

坑在哪：
  1. 题面明说**没有 SPJ**，必须按 l 递增输出。
     由于 lo(r) 在长度相同时随 r 严格递增，按 r 从小到大输出天然满足；
  2. a_i 的范围是 0..n（含 0），last 数组要开 n+1 长；
  3. 答案区间至少有一个（单个元素总是合法），不必特判空；
  4. 输出量最大 2e5 行，用 "\\n".join 一次性写出。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    a = list(map(int, data[1:1 + n]))
    last = [-1] * (n + 1)                    # a_i ∈ [0, n]
    lo = [0] * n                             # lo[r] = 以 r 结尾的最长合法区间左端（0-indexed）
    l = 0
    best = 0
    for r in range(n):
        v = a[r]
        j = last[v]
        if j >= l:                           # v 在窗口内出现过，左端跳过去
            l = j + 1
        last[v] = r
        lo[r] = l
        if r - l + 1 > best:
            best = r - l + 1
    out = []
    push = out.append
    for r in range(n):
        if r - lo[r] + 1 == best:
            push("%d %d" % (lo[r] + 1, r + 1))
    sys.stdout.write("%d\n%s\n" % (len(out), "\n".join(out)))


main()

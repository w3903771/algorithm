"""BISHI125 【模板】静态区间最值 —— 只有查询、没有修改的区间 min / max。

这题考什么：
    区间数据结构的选型第一课：**只查不改就别写线段树，用 ST 表**
    （sparse table，稀疏表：预处理所有「起点任意、长度为 2 的幂」的区间最值）。
        预处理 O(n log n)，查询 **O(1)**。
    原理是倍增 + 「可重复贡献」：st[k][i] = [i, i+2^k) 的最值，
        st[k][i] = f(st[k-1][i], st[k-1][i + 2^(k-1)])
    查询 [l, r] 时取 k = floor(log2(r-l+1))，用**两个可重叠**的长度 2^k 区间覆盖：
        f(st[k][l], st[k][r - 2^k + 1])
    最值满足 f(x, x) = x，重叠不影响答案；求和就不行（会算两遍）。

数据规模与复杂度：
    n, q <= 5e5，需要两张表（min 一张、max 一张），各 19 层。
    时限「其他语言 10 秒」、空间「其他语言 2048M」——出题人显然给非 C++ 留了余地。

Python 关键（这是能不能过的分水岭）：
  1. **整层用 `list(map(min, p, p[h:]))` 在 C 层构建**。
     `map` 遇到较短的迭代器就停，自动截断到正确长度；
     写成 `[min(p[i], p[i+h]) for i in range(...)]` 会慢 5 倍，直接超时；
  2. 查询里**内联 min/max**（写成 `x if x < y else y`），
     省掉 1e6 次内置函数调用，约快 20%；
  3. 只有两级索引 `mn[j][l]`，不要建三维结构。

坑在哪：
  1. 下标从 1 开始，内部一律转 0-indexed；
  2. a_i 可以是负数，别用 0 当初值；
  3. k = (r-l+1).bit_length() - 1 就是 floor(log2(len))，不需要预处理 log 表。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); q = int(data[1])
    a = list(map(int, data[2:2 + n]))

    # ---- 建表：第 0 层就是原数组，第 k 层的每项覆盖长度 2^k ----
    mn = [a]                                 # 两张 ST 表，整层用 map 在 C 层构建
    mx = [a]
    k = 1
    while (1 << k) <= n:                     # 只建到最长可用的那层为止
        h = 1 << (k - 1)                     # 上一层的跨度，也是右半段的偏移
        p = mn[-1]
        # st[k][i] = f(st[k-1][i], st[k-1][i+h])；
        # map 遇到较短的 p[h:] 就停，长度自动收敛到 len(p)-h，正好是本层的合法项数
        mn.append(list(map(min, p, p[h:])))
        p = mx[-1]
        mx.append(list(map(max, p, p[h:])))
        k += 1

    # ---- 回答询问 ----
    p = 2 + n
    out = []
    push = out.append
    for _ in range(q):
        op = data[p]                         # 保持 bytes，与 b"1" 直接比，省一次解码
        l = int(data[p + 1]) - 1             # 转 0-indexed
        r = int(data[p + 2]) - 1
        p += 3
        j = (r - l + 1).bit_length() - 1     # floor(log2(区间长))，不必预处理 log 表
        s = r - (1 << j) + 1                 # 右半段的起点，与左半段允许重叠
        if op == b"1":                       # 区间最小
            row = mn[j]
            x = row[l]; y = row[s]
            push(x if x < y else y)          # 内联比较，省掉 5e5 次内置函数调用
        else:                                # 区间最大
            row = mx[j]
            x = row[l]; y = row[s]
            push(x if x > y else y)
    sys.stdout.write("\n".join(map(str, out)) + "\n")


main()

"""BISHI115 可匹配子段计数 —— 统计 a 中有多少个长度为 m 的子段与 b 的「匹配度」>= k。

这题考什么：
    题面已经把匹配度化简好了：
        match(c) = Σ_x min(cnt_x(c), cnt_x(b))
    （因为 c 可以任意重排，能对上的位置数就是每种值取两边计数的较小者之和。）
    于是问题变成「长度固定的滑动窗口 + 增量维护一个统计量」——定长双指针。

    增量维护是关键：
      - 加入元素 x：若加入**前** cnt_win[x] < cnt_b[x]，说明这一个 x 能新配上一位，
        match += 1；否则 x 已经多余，match 不变；
      - 删除元素 x：若删除**前** cnt_win[x] <= cnt_b[x]，说明它原本是配上的，
        match -= 1。
    两个判断的等号位置正好互补，写反就会漂移。

数据规模与复杂度：
    t <= 1e4，但保证 Σn、Σm <= 2e5，所以总复杂度 O(Σn)。
    a_i <= 1e6，用**字典**计数而不是 1e6 长的数组——否则每组用例都要清空 1e6 个格子，
    1e4 组就是 1e10 次赋值。

坑在哪：
  1. m 可能等于 n（只有一个子段），也可能 m=1，边界都要能跑；
  2. 匹配度是「>= k」，不是「= k」；
  3. 多组数据必须用一个游标顺序解析，不能按行读。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    p = 0
    t = int(data[p]); p += 1
    out = []
    push = out.append
    for _ in range(t):
        n = int(data[p]); m = int(data[p + 1]); k = int(data[p + 2])
        p += 3
        a = data[p:p + n]                    # 保持 bytes，可直接当字典键，省去 int 转换
        p += n
        b = data[p:p + m]
        p += m

        # need[x] = x 在 b 中的出现次数，也就是「x 最多能贡献几个匹配位」
        need = {}
        for x in b:
            need[x] = need.get(x, 0) + 1
        have = {}                            # 当前窗口内各值的计数
        match = 0                            # 当前窗口的匹配度 Σ min(have, need)
        ans = 0
        for i in range(n):
            # ---- 右端进入 a[i] ----
            x = a[i]
            h = have.get(x, 0)               # 注意取的是**加入前**的计数
            if h < need.get(x, 0):           # 这一个 x 还能配上一位
                match += 1
            have[x] = h + 1                  # 已经配满则只增计数，match 不动
            # ---- 左端弹出：窗口长度回到 m ----
            if i >= m:                       # 窗口超长，弹出左端
                y = a[i - m]
                h = have[y]                  # 同样是**删除前**的计数
                if h <= need.get(y, 0):      # 弹掉的这个原本是配上的
                    match -= 1
                have[y] = h - 1
            # ---- 窗口首次填满是 i = m-1，此后每一步都是一个候选子段 ----
            if i >= m - 1 and match >= k:
                ans += 1
        push(ans)
    sys.stdout.write("\n".join(map(str, out)) + "\n")


main()

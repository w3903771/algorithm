"""BISHI36 【模板】扩展巴什博弈 —— 每次取 l..r 个，取到最后一个者胜；不足 l 则不能取。

这题考什么：
    扩展巴什博弈的结论：
        先手必胜 <=> n mod (l + r) >= l。
    推导：剩余石子 s 落在 [0, l-1] 时当前行动者无法取子，直接判负，
    所以这 l 个数是「必败区」。以 l + r 为周期考察：
      - 若 s mod (l+r) ∈ [l, r]，先手可以一次取到 s' 使 s' mod (l+r) 落回
        必败区（比如取 s mod (l+r) 颗，取子量在 [l, r] 内，合法）；
      - 若 s mod (l+r) ∈ [0, l-1]，先手取 x ∈ [l, r] 后
        (s - x) mod (l+r) ∈ [l+r-r, l+r-l] 平移到 [l, r] 区间，
        也就是把必胜态还给对手；这样一路下去先手最终面对 [0, l-1] 而输。
    注意 r 可以大于 l+r-1 之类的边界这里被 mod 自动吸收。

    特例自然覆盖：n < l 时 n mod (l+r) = n < l，输出 NO（无法行动即负）。

数据规模与复杂度：
    T <= 2e6，n,l,r <= 1e9。每组 O(1)，瓶颈是 IO：
    输入 6e6 个 token、输出 2e6 行，必须整块读入 + 一次性写出。

坑在哪：
    1. 判定用的模数是 l + r，不是 r + 1（那是普通巴什博弈的特例 l = 1）；
    2. n < l 一定是 NO，公式已经覆盖，别再画蛇添足写反；
    3. 样例第三组 n=7,l=2,r=5：7 mod 7 = 0 < 2 -> NO，正好卡在整除边界。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    out = []
    p = 1
    for _ in range(t):
        n = int(data[p]); l = int(data[p + 1]); r = int(data[p + 2]); p += 3
        out.append("YES" if n % (l + r) >= l else "NO")
    sys.stdout.write("\n".join(out) + "\n")


main()

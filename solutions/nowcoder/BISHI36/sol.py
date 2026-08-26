"""BISHI36 【模板】扩展巴什博弈 —— 每次取 l..r 个，取到最后一个者胜；不足 l 则不能取。

这题考什么：
    扩展巴什博弈的结论：
        先手必胜 <=> n mod (l + r) >= l。
    推导：把剩余石子数按 l + r 取模来分类，余数 c 的取值范围是 [0, l+r-1]。
    若剩余石子落在 [0, l-1]，当前行动者连最少的 l 颗都取不走，直接判负，
    所以余数区间 [0, l-1] 是「必败区」，其余的 [l, l+r-1] 是「必胜区」。
      - 余数 c ∈ [l, l+r-1] 时，取走 x = min(c, r) 颗即可：x 落在 [l, r] 内，
        是合法取子量；取完后余数变成 c - x ∈ [0, l-1]，必败区被丢给对手。
        （c <= r 时一步把余数清成 0；c > r 时取满 r 颗，余数 c - r <= l - 1。）
      - 余数 c ∈ [0, l-1] 时，无论取 x ∈ [l, r] 里的哪一个，
        新余数 (c - x) mod (l+r) = c - x + (l+r) 都落在 [l, l+r-1]，
        也就是只能把必胜区还给对手。
    两条合起来即得：先手必胜 <=> n mod (l+r) >= l。
    必胜态与必败态的一般分析方法见 docs/math/game/impartial.md。

    特例自然覆盖：n < l 时 n mod (l+r) = n < l，输出 NO（无法行动即负）。

数据规模与复杂度：
    T <= 2e6，n,l,r <= 1e9。每组 O(1)，瓶颈是 IO：
    输入 6e6 个 token、输出 2e6 行，必须整块读入 + 一次性写出。

坑在哪：
    1. 判定用的模数是 l + r，不是 r + 1（那是普通巴什博弈的特例 l = 1）；
    2. n < l 一定是 NO，而 n mod (l+r) = n < l 已经覆盖了这种情况，
       再额外加一个 if 反而容易把方向写反；
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
        # 余数落在必胜区 [l, l+r-1] 则先手赢，落在必败区 [0, l-1] 则先手输
        out.append("YES" if n % (l + r) >= l else "NO")
    sys.stdout.write("\n".join(out) + "\n")


main()

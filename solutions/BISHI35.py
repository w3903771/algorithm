"""BISHI35 【模板】巴什博弈 —— n 个石子每次取 1..m 个，取到最后一个者胜。

这题考什么：
    巴什博弈（Bash Game）的标准结论：
        先手必败 <=> (m + 1) | n。
    理由：把石子按 m+1 一组切分。若 n 是 m+1 的倍数，无论先手取 x(1<=x<=m)，
    后手都能取 (m+1-x) 把这一组补满，局面永远回到「剩余是 m+1 的倍数」，
    最终后手拿走最后一颗；反之先手第一步先取 n mod (m+1) 颗，
    把局面变成上述必败态丢给对手。
    这条「凑成固定周期」的补数思路是博弈论构造题的通用起手式，
    见 docs/part4-基础算法/50-博弈论.md。

数据规模与复杂度：
    T <= 2e6，n,m <= 1e9。**每组 O(1)，瓶颈完全在 IO**：
    输入 token 有 4e6 个、输出有 2e6 行。
    所以必须 sys.stdin.buffer.read().split() 整块读入，
    输出攒成 list 后一次 "\\n".join 写出；
    逐行 input()/print() 在这个量级会直接 TLE。

坑在哪：
    1. 是 (m+1) | n 判负，不是 m | n；
    2. m 可能大于等于 n，此时 n mod (m+1) = n != 0（n>=1），先手一次拿光必胜，
       结论自动覆盖，不用特判（样例第一组 n=3,m=5 即是）；
    3. 输出是 YES / NO 大写。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    out = []
    p = 1
    for _ in range(t):
        n = int(data[p]); m = int(data[p + 1]); p += 2
        # 余数非 0 即先手必胜；余数为 0（也就是 (m+1) | n）先手必败
        out.append("YES" if n % (m + 1) else "NO")
    sys.stdout.write("\n".join(out) + "\n")


main()

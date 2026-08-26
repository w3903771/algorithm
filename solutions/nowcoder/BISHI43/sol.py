"""BISHI43 讨厌鬼进货 —— 每种货物在 A/B 二选一，或者花 x 元网购全部。

这题考什么：
    网购是「全有或全无」：一旦买了，n 种货物就全齐了，再买别的只是浪费。
    所以方案只有两类：
      1. 完全不网购 —— 每种货物独立地取 min(a_i, b_i)，总价 Σ min(a_i, b_i)；
      2. 网购 —— 花 x 元，一次搞定。
    答案 = min(x, Σ min(a_i, b_i))。

    样例：Σ min = 1+1+1+1+2 = 6，x = 5，取 5。

数据规模与复杂度：
    n <= 1e5，a_i,b_i <= 1e4，x <= 1e9。O(n) 一遍扫完，不需要排序，也不需要 DP。
    总和最大 1e5 * 1e4 = 1e9，仍在 int 范围内（C/C++ 用 int 也刚好够，
    但建议 long long；Python 无所谓）。
    输入共 2e5 + 2 个整数，逐行 input() 的解析开销明显高于整块读，
    统一用 sys.stdin.buffer.read()。

坑在哪：
    1. 别以为「网购 + 单买」能混出更便宜的方案 —— 网购已经覆盖全部品类，
       任何额外购买都只增不减；
    2. 逐项取 min 而不是「a 全买 或 b 全买」二选一，供应商是可以混着用的：
       第 1 种在 A 家便宜、第 2 种在 B 家便宜时两家都要光顾；
    3. x 与 Σ min 两个候选都要算完再比。只看 x 和单个 a_i/b_i 的大小关系
       得不出结论：x 便宜与否取决于全部 n 项的总和；
    4. 三行输入，用 buffer.read().split() 整块读 + 切片最省事。

    贪心的一般套路见 docs/basic/greedy.md。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); x = int(data[1])
    # 两段价格表按已知长度切片；这里仍是 bytes，等到比较时才逐个转 int，
    # 省掉一次「先整体转成 int 列表」的中间列表
    a = data[2:2 + n]
    b = data[2 + n:2 + 2 * n]
    # 每种货物在两家供应商之间独立取便宜的那家，累加得到「完全不网购」的花费
    s = sum(min(int(p), int(q)) for p, q in zip(a, b))
    # 全部方案只有「不网购」和「网购」两类，取较小者
    print(min(x, s))


main()

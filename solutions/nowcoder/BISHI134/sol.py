"""BISHI134 最大子段和 —— 选一个非空连续子数组使元素和最大。

这题考什么：
    Kadane 算法（最大子段和的线性 DP）。设 f_i = 「以 i 结尾」的最大子段和：
        f_i = a_i + max(f_{i-1}, 0)
    含义：要么把前面那段接上（前提是它是正贡献），要么从 i 重新开始。
    答案 = max f_i。

    等价视角：设前缀和 S，则答案 = max_{i} (S_i - min_{j<i} S_j)，
    也就是「一边扫一边记录历史最小前缀和」。两种写法完全等价。

数据规模与复杂度：
    n <= 2e5，O(n) 时间、O(1) 空间。
    枚举左右端点是 O(n^2) = 4e10，必挂。

坑在哪：
  1. **要求非空**，所以答案初值必须是 a_1（或 -inf），不能是 0——
     全负数组时答案是最大的那个负数，初值取 0 会错误地输出 0；
  2. a_i 可以是负数，`max(f, 0)` 的 0 是「放弃前面这段」而不是「和为 0 的空段」，
     因为 f_i 里必定含 a_i，非空性有保证；
  3. n = 1 时直接输出 a_1。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    cur = best = int(data[1])                # 非空 -> 初值必须是第一个元素，不能是 0
    # cur 是「以当前元素结尾」的最大子段和，best 是扫到目前为止的全局最大值。
    # 首元素已经吃掉，所以从 data[2] 开始，切片右端 1 + n 正好是最后一个元素的下一位
    for tok in data[2:1 + n]:
        x = int(tok)
        cur = x + cur if cur > 0 else x      # 前面那段是负贡献就丢掉
        if cur > best:                       # 逐个比较即可，不必最后再 max 一遍
            best = cur
    sys.stdout.write("%d\n" % best)


main()

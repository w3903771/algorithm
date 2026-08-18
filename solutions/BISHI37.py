"""BISHI37 数位差与数值和的构造 —— 把 n 拆成 x+y，使两者数字和之差的绝对值 <= 1。

这题考什么：
    关键观察：**只要拆分「不产生进位」，数字和就是可加的**。
    把 n 的十进制写成 d_{k-1}...d_0，如果对每一位取 p_i + q_i = d_i
    （0 <= p_i, q_i <= 9），那么 x = Σ p_i·10^i，y = Σ q_i·10^i 满足
    x + y = n，且 digitsum(x) + digitsum(y) = Σ d_i = S 恰好等于 n 的数字和。

    于是问题变成「把总量 S 劈成两半」：目标 t = S // 2，
    从高位到低位贪心，每位尽量多分给 x：p_i = min(d_i, 剩余额度)。
    最终 digitsum(x) = t，digitsum(y) = S - t，两者差 = S mod 2 <= 1。

    这也顺带证明了题面所说「解一定存在」。

数据规模与复杂度：
    t <= 1e4，n <= 1e9（最多 10 位）。每组 O(位数) = O(10)，总计 1e5 级别。
    完全不需要枚举 x（那是 1e9 次）。

坑在哪：
    1. 必须按「无进位拆分」来做，随便找个 x 再算 y = n-x 会产生借位，
       数字和的可加性就没了；
    2. y 允许为 0（题面说的是非负整数，不是正整数），n=1 时输出 "0 1" 合法；
    3. x 的高位可能是 0（比如 n=1206 得到 x=1201, y=0005=5），
       转成 int 输出即可，不能带前导零；
    4. 答案不唯一：题目只约束 x + y = n 与两边数字和之差不超过 1，
       满足条件的拆法通常有很多组（n = 161 时样例给 67 94，本解法给 130 31，
       两者数字和之差都不超过 1）。所以本地要用 special judge（特殊评测程序，
       按题目条件验证选手输出是否合法，而不是与标准答案逐字符比对）：
       本题配了 solutions/_spj/BISHI37.py，它逐组检查 x、y 非负、x + y == n，
       并真的把两边的数字和算出来比较差值。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    out = []
    for i in range(1, t + 1):
        s = data[i]
        digits = [c - 48 for c in s]          # bytes 逐字节即 ASCII 码
        need = sum(digits) // 2               # x 要拿走的数字和（下取整）
        xd = []
        for d in digits:
            take = d if d <= need else need   # 每位尽量多给 x，且不超过本位数值
            need -= take
            xd.append(take)
        x = int("".join(map(str, xd)))
        out.append("%d %d" % (x, int(s) - x))
    sys.stdout.write("\n".join(out) + "\n")


main()

"""BISHI33 Poi 的新加法（Easy） —— 区间上左折叠 f(x,y) = x + y - (x xor y)。

这题考什么：
    先把 f 化简。经典恒等式 x + y = (x xor y) + 2*(x and y)，代入得
        f(x, y) = x + y - (x xor y) = 2 * (x and y)。
    也就是「按位与之后左移一位」，正好对应题面「只进一次位」的描述。

    Easy 版限定 q = 1 且 l = 1, r = n，也就是每组只问一次整段折叠：
        res = a_1;  res = 2*(res and a_i)  依次对 i = 2..n 做。
    直接顺序模拟即可，n = 1 时结果就是 a_1（没有任何一次 f）。

    （顺带一提为什么不能预处理前缀：f 不满足结合律，
      2*(2*(a&b) & c) 与 2*(a & 2*(b&c)) 不同，所以只能老实从左往右扫；
      Hard 版才需要利用「每折叠一次值就左移一位、最多 60 次后必然归零」的
      性质做区间处理。）

数据规模与复杂度：
    T <= 1e6，∑n <= 1e6，∑q <= 1e6，a_i < 2^60。
    总复杂度 O(∑n)，但 **IO 是瓶颈**：token 数量级 3e6，
    必须 sys.stdin.buffer.read().split() 一次读完 + 游标推进，
    输出攒 list 最后一次 write。

坑在哪：
    1. 折叠结果最大会到 2^61，C/C++ 里 int 会溢出，Python 无所谓；
    2. n 可以等于 1，此时答案就是 a_1，循环要能正确退化；
    3. 每组末尾还有 q 行 l r 必须读掉（虽然恒为 1 和 n），
       不读会导致游标错位、后面全乱；
    4. 中间值只会「越折越左移」，但不能因此提前 break —— 一旦某步与出 0，
       后面恒为 0，倒是可以剪枝，这里 n 之和才 1e6，不必要。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    p = 0
    T = int(data[p]); p += 1
    out = []
    for _ in range(T):
        n = int(data[p]); q = int(data[p + 1]); p += 2
        base = p                           # 记下本组序列的起始位置
        p += n                             # 游标先跳过整段序列，后面直接按 base 取值
        res = int(data[base])              # 左折叠的初值就是 a_1；n = 1 时它即为答案
        for i in range(base + 1, base + n):
            res = 2 * (res & int(data[i]))     # f(x, y) = 2 * (x & y)
        for _ in range(q):
            p += 2                             # l, r 恒为 1 和 n，读掉即可
            out.append(str(res))
    sys.stdout.write("\n".join(out) + "\n")


main()

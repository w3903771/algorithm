"""BISHI64 【模板】快速幂Ⅰ ‖ 模小整数 —— T 组询问，每组求 a^b mod p。

这题考什么：
    快速幂模板。但在 Python 里正确答案是：**直接用内置 pow(a, b, m)**。
    CPython 的三参数 pow 就是 C 层实现的模幂（对大指数还会自动切到
    5-bit 滑动窗口），比任何手写 while b: ... b >>= 1 的 Python 循环快一个量级。
    手写快速幂在这里纯属自我惩罚：2e5 组 * 30 轮 = 6e6 次 Python 层迭代。

数据规模与复杂度：
    T <= 2e5，a,b <= 1e9，p <= 1e9。
    每组 O(log b) 次模乘，全部下沉到 C；瓶颈反而是 IO 和 int() 解析，
    所以必须整块读 + 一次性输出。

坑在哪：
  1. **p 可以等于 1**！此时任何数模 1 都是 0，样例第一行 "1 0 1" 的答案就是 0。
     手写快速幂如果把 res 初始化成 1 而忘了最后 % p，就会错输出 1。
     内置 pow 不会有这个问题（pow(1, 0, 1) == 0）；
  2. a 可以为 0（题目只保证 a + b > 0，所以 0^0 这种组合被排除了），
     pow(0, b, p) 对 b >= 1 正确返回 0；
  3. T 到 2e5，逐行 input() 会超时，必须缓冲读。
"""
import sys


def main() -> None:
    # 一次性读完整个输入再按空白切分，2e5 组数据下比逐行 input() 快一个量级
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    out = []
    ap = out.append                  # 提前绑定 append，省掉循环里每轮的属性查找
    idx = 1                          # data[0] 是组数，真正的数据从下标 1 开始

    # 逐组取 (a, b, p)：三个数一组，用一个游标扫过去，不做切片拷贝
    for _ in range(t):
        a = int(data[idx]); b = int(data[idx + 1]); p = int(data[idx + 2])
        idx += 3                     # 游标整体后移一组
        ap(str(pow(a, b, p)))        # 内置三参数 pow = C 实现的快速幂，p=1 自动给 0

    # 全部答案拼成一整块再写出，避免 2e5 次系统调用
    sys.stdout.write("\n".join(out) + "\n")


main()

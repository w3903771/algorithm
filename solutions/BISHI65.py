"""BISHI65 【模板】分数取模 —— 求 a/b mod P，P = 1e9+7 为质数，a 可能为负。

这题考什么：
    模意义下的除法 = 乘以乘法逆元。P 是质数，由费马小定理
        b^(P-1) ≡ 1 (mod P)  =>  b^(-1) ≡ b^(P-2) (mod P)（要求 P 不整除 b）
    所以 a/b mod P = a * pow(b, P-2, P) mod P。

    Python 3.8 起 pow 支持负指数：pow(b, -1, P) 会直接用扩展欧几里得算逆元，
    3.9 当然也支持，而且不要求模数是质数（只要 gcd(b,P)=1）。
    本题两种写法都对；这里用 pow(b, P-2, P) 以贴合「质模数 + 费马小定理」的模板，
    并在下面注释里给出 pow(b, -1, P) 的等价写法。

数据规模与复杂度：
    t <= 1e4，每组一次模幂 O(log P) 全在 C 层，总耗时可忽略，瓶颈是 IO。

坑在哪：
  1. **a 可能是负数**（-1e9 <= a <= 1e9）。Python 的 % 永远返回非负结果，
     所以 a * inv % P 天然落在 [0, P-1]，不用像 C++ 那样 ((x % P) + P) % P；
  2. b 的范围是 1 <= b <= 1e9 < P，所以 b mod P != 0，逆元一定存在，
     不需要判 b ≡ 0 的退化情形；
  3. 别真的去算浮点 a/b 再取模，那是完全不同的东西。
"""
import sys

P = 1000000007


def main() -> None:
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    out = []
    ap = out.append
    for i in range(t):
        a = int(data[1 + 2 * i]); b = int(data[2 + 2 * i])
        # 等价写法：inv = pow(b, -1, P)（Python 3.8+，走扩展欧几里得，不要求 P 是质数）
        ap(str(a * pow(b, P - 2, P) % P))     # Python 的 % 天然把负数拉回 [0,P)
    sys.stdout.write("\n".join(out) + "\n")


main()

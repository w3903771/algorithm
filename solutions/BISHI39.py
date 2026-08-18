"""BISHI39 【模板】Pollard-Rho 算法 —— 判定 x (<= 1e12) 是否为质数。

这题考什么：
    题目挂着 Pollard-Rho 的名字，但真正问的只是**素性判定**，
    并不需要把 x 分解出来，所以核心是 Miller-Rabin。
    （Pollard-Rho 是「找非平凡因子」的算法，它内部还要靠 Miller-Rabin
      判断递归边界；这里既然只要 Yes/No，就没必要真去分解。）

    Miller-Rabin：把 n-1 写成 d * 2^s（d 为奇数），对底数 a 检查
        a^d ≡ 1 (mod n)  或  存在 0 <= r < s 使 a^(d·2^r) ≡ -1 (mod n)，
    否则 n 必为合数。Python 的内置 pow(a, d, n) 就是 C 实现的快速幂，
    自带模乘，不用手写龟速乘（C++ 里 1e12 的模乘会爆 long long，
    要用 __int128 或 Montgomery，Python 完全没这个烦恼）。

    **确定性底数**：已知对 n < 3,474,749,660,383（约 3.47e12）而言，
    底数集合 {2,3,5,7,11,13} 的 Miller-Rabin 是**确定性**的、不会误判。
    本题 x <= 1e12 < 3.47e12，所以直接用这 6 个底数即可。
    这样一来算法里**完全没有随机数**，同一输入多次运行结果必然一致，
    也不存在「随机种子导致偶发 WA」的问题。

数据规模与复杂度：
    T <= 1e5，x <= 1e12。
    单次 Miller-Rabin 是 O(k log x) 次模乘（k = 6，log x ≈ 40）。
    优化两处以压常数：
      1. 先用小素数（< 100）试除，绝大多数合数在这里就被筛掉，
         只有少数「大素数 / 大半素数」才走到 Miller-Rabin；
      2. 用字典缓存已算过的 x（T 到 1e5 时重复询问很常见）。
    IO 用 buffer.read().split()，输出攒 list 一次写出。

坑在哪：
    1. x = 1 不是质数，必须特判（n-1 = 0 会让 Miller-Rabin 逻辑失效）；
    2. 底数 a 可能等于 n 本身（例如 n = 2,3,5,7,11,13），
       此时 a % n == 0，要先把这些小素数直接判 Yes 再进主流程；
    3. 输出是 Yes / No（首字母大写，其余小写），不是 YES/NO；
    4. Python 3.9 兼容：pow 的三参数形式（模幂）从 2.x 就有，不依赖新版本特性；
    5. 内层循环写成 for ... else：只有当循环**没有被 break 打断**时才执行 else，
       正好对应「s-1 次平方里始终没出现 n-1」这一判合数的条件。
       误把 else 缩进到 for 内部或写成 if，判定就会反过来。

    快速幂与模运算见 docs/part7-数学/81-快速幂与逆元.md，
    素数与因数的基础见 docs/part7-数学/80-数论基础.md。
"""
import sys

SMALL = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
         53, 59, 61, 67, 71, 73, 79, 83, 89, 97)
# 对 n < 3.47e12 而言，这组底数的 Miller-Rabin 是确定性的
BASES = (2, 3, 5, 7, 11, 13)


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    for p in SMALL:
        if n % p == 0:
            return n == p              # 小素数本身算质数，其余倍数直接判负
    # 把 n-1 分解成 d * 2^s，其中 d 为奇数（Miller-Rabin 的标准预处理）
    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in BASES:
        x = pow(a, d, n)               # 内置快速幂，C 实现
        if x == 1 or x == n - 1:
            continue                   # 该底数已通过，换下一个
        for _ in range(s - 1):
            x = x * x % n              # 逐次平方，走完 a^(d*2^r) 这条链
            if x == n - 1:
                break                  # 出现 -1，该底数通过
        else:
            return False               # 没有出现 -1，判定为合数
    return True


def main() -> None:
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    cache = {}
    out = []
    for i in range(1, t + 1):
        x = int(data[i])
        r = cache.get(x)               # T 到 1e5 时重复询问常见，命中即省一次判定
        if r is None:
            r = "Yes" if is_prime(x) else "No"
            cache[x] = r
        out.append(r)
    sys.stdout.write("\n".join(out) + "\n")


main()

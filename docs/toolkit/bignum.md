---
id: toolkit/bignum
title: 高精度与大整数
volume: 1
lang: py
---

# 第 22 章　高精度与大整数

<!-- CHAPTER-EXAMPLES -->

C++ 选手要为高精度写四份模板，Python 选手一行都不用写——`int` 本身就是任意精度的。
这一章的重点因此不是「怎么实现高精度」，而是**「什么时候 Python 的大整数是优势，什么时候是陷阱」**。

---

## 1　Python 的整数没有上限

```python
>>> import math
>>> math.factorial(100)
93326215443944152681699238856266700490715968264381621468592963895217599993229915608941463976156518286253697920827223758251185210916864000000000000000000000000
>>> 2 ** 4096 % (10 ** 9 + 7)
430631182
```

对照 C++ 的四个高精度模板（加、减、乘、除），Python 的等价物是：

| 高精度操作 | C++ 需要 | Python |
| --- | --- | --- |
| 加法 | ~40 行 | `a + b` |
| 减法 | ~45 行 | `a - b` |
| 乘法 | ~35 行 | `a * b` |
| 除法（高精除单精） | ~30 行 | `a // b` |
| 取模 | 另写 | `a % b` |
| 幂 | 快速幂 + 高精乘 | `a ** b` 或 `pow(a, b, m)` |
| 比较 | 逐位比较 | `a < b` |
| 转字符串 | 逐位输出 | `str(a)` |

**所以凡是题面里出现「$a, b \le 10^{500}$」「求 $n!$ 的精确值」这类描述，
Python 选手可以直接跳过整个高精度章节。**

---

## 2　代价：大整数运算不是 $O(1)$

这是必须警惕的另一面。CPython 的 `int` 内部是 30 位一个「肢」（limb）的数组，
所以运算复杂度取决于位数 $d$：

| 运算 | 复杂度 |
| --- | --- |
| `a + b`、`a - b` | $O(d)$ |
| `a * b` | $O(d^{1.585})$（Karatsuba，$d$ 大时）；小数时 $O(d^2)$ |
| `a // b`、`a % b` | $O(d^2)$ 量级 |
| `str(a)`、`int(s)` | $O(d^2)$ ← **特别慢** |
| `pow(a, b, m)` | $O(\log b)$ 次模乘 |

两条实战准则：

### 准则一：能取模就立刻取模

```python
# ❌ 中间值疯狂膨胀：每乘一次位数就涨一截，乘法复杂度跟着位数一起涨
res = 1
for i in range(1, n + 1):
    res *= i
print(res % MOD)          # 到这里 res 已经是几百万位，取模也救不回前面的时间

# ✅ 每步取模：乘之前两边都 < MOD，乘完最大也只有 MOD² 那么大，一取模又缩回去
res = 1
for i in range(1, n + 1):
    res = res * i % MOD   # 先乘后模；先模后乘会漏掉 i 本身超过 MOD 的情况
print(res)
```

$n = 10^6$ 时，前者的 `res` 会膨胀到约 550 万位，光是那些乘法就要跑几分钟；
后者始终是 60 位以内的小整数，秒出。

### 准则二：`str(bigint)` 和 `int(bigstr)` 很贵

十进制转换是 $O(d^2)$ 的。$10^6$ 位的数转字符串要几十秒。
需要输出超大数时，考虑题目是不是真的要十进制（有时可以输出十六进制或取模值）。

> **Python 3.11+ 的额外限制**：出于 DoS 防护，`int(s)` 默认最多接受 4300 位字符串，
> `str(n)` 也有对应限制，超了抛 `ValueError: Exceeds the limit for integer string conversion`。
> 解除方法：
> ```python
> import sys
> sys.set_int_max_str_digits(0)     # 0 表示不限制
> ```
> Python 3.9 没有这个限制，但牛客判题机的版本未知，**写超大数十进制输出的题时加上这一句更保险**
> （在 3.9 上调用会 `AttributeError`，所以要包一层 `try`）：
> ```python
> try:
>     sys.set_int_max_str_digits(0)
> except AttributeError:
>     pass
> ```

---

## 3　需要手写高精度的场景

Python 里几乎没有。唯一的例外是**题目要求实现某种自定义的进位规则**——
这时「高精度」的形式还在，但语义变了。BISHI33 就是这样一道题。

作为教学，这里给出一份按经典模板结构组织的十进制高精度实现，
**仅供理解原理，实战中不要用**：

```python
def add(a, b):
    """高精度加法。a, b 为低位在前的十进制数位列表。"""
    n = max(len(a), len(b))               # 和至少和较长的加数一样长
    res, carry = [], 0                    # carry 是上一位进上来的值，只可能是 0 或 1
    for i in range(n):
        s = carry                         # 本位的和 = 进位 + 两个加数的本位
        if i < len(a):
            s += a[i]                     # 短的那个数在高位视为 0
        if i < len(b):
            s += b[i]
        res.append(s % 10)                # 个位留在本位
        carry = s // 10                   # 十位进到下一轮
    if carry:
        res.append(carry)                 # 最高位还有进位时，结果比两个加数都长一位
    return res


def sub(a, b):
    """高精度减法，要求 a >= b。"""
    res, borrow = [], 0                   # borrow 是上一位向本位借走的 1
    for i in range(len(a)):
        d = a[i] - borrow - (b[i] if i < len(b) else 0)   # 减数在高位视为 0
        borrow = 0
        if d < 0:                         # 不够减，就向更高位借 10
            d += 10
            borrow = 1                    # 借了就记账，下一轮扣回去
        res.append(d)
    while len(res) > 1 and res[-1] == 0:      # 去前导零
        res.pop()                         # 长度保留至少 1 位，结果为 0 时留下 [0]
    return res


def mul(a, b):
    """高精度乘法，O(len(a) * len(b))。"""
    res = [0] * (len(a) + len(b))         # 乘积位数不会超过两个乘数的位数之和
    for i, x in enumerate(a):
        if x == 0:
            continue                      # 本位为 0，整轮内层循环都是加 0，跳过
        carry = 0
        for j, y in enumerate(b):
            cur = res[i + j] + x * y + carry   # 下标 i+j：x*y 的权重正是 10^(i+j)
            res[i + j] = cur % 10
            carry = cur // 10             # 这里的进位最大到 8，不是 1，必须整除取
        res[i + len(b)] += carry          # 内层走完后把剩余进位落到更高一位
    while len(res) > 1 and res[-1] == 0:  # 预留的长度可能多一位，去掉前导零
        res.pop()
    return res


def divmod_small(a, b):
    """高精度除以单精度，返回 (商列表, 余数)。"""
    res, r = [0] * len(a), 0              # r 是上一位除完剩下的余数
    for i in range(len(a) - 1, -1, -1):   # 竖式除法从最高位算起，所以下标倒着走
        cur = r * 10 + a[i]               # 余数左移一位，接上当前这一位
        res[i] = cur // b                 # 商写回同一个下标，商的位数不会超过被除数
        r = cur % b                       # 余数继续带到下一位
    while len(res) > 1 and res[-1] == 0:  # 商的高位可能是 0，去掉
        res.pop()
    return res, r


def to_digits(s):
    """字符串 -> 低位在前的数位列表。"""
    return [int(c) for c in reversed(s.strip())]   # 反过来存，下标 i 就是 10^i 位


def to_str(a):
    return "".join(map(str, reversed(a)))          # 再翻回高位在前，才是人读的顺序
```

对照一下真正该写的代码：

```python
print(int(input()) + int(input()))        # 这就是全部：int 本身就是任意精度
```

---

## 4　例题

<!-- CHAPTER-EXAMPLE-TABLE -->

### BISHI63 计算阶乘（简单）

> 给定 $T \le 10^3$ 个正整数 $n \le 10^6$，求 $n! \bmod (10^9+7)$。

这题把 §2 的两条准则都考到了。

**朴素做法**（每次询问重算）的复杂度是 $O(T \cdot n) = 10^9$，必然 TLE。
正确做法是**预处理阶乘前缀表**，之后每次询问 $O(1)$：

```python
import sys

MOD = 10 ** 9 + 7
MAXN = 10 ** 6


def main():
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    ns = list(map(int, data[1:1 + t]))        # t 个询问一次读完，后面要先取 max

    lim = max(ns)                             # 只预处理到实际用到的最大 n
    fact = [1] * (lim + 1)                    # fact[i] 存 i! mod MOD；fact[0] = 1 是边界
    for i in range(1, lim + 1):
        fact[i] = fact[i - 1] * i % MOD       # ← 每步取模，中间值始终小于 MOD²

    # 表建好之后每次询问就是一次下标寻址，O(1)
    sys.stdout.write("\n".join(str(fact[n]) for n in ns) + "\n")


main()
```

三个要点：

1. **每步 `% MOD`**。不取模的话 `fact[10**6]` 有 550 万位，光内存就爆。
2. **只预处理到 $\max n$**，不是固定 $10^6$——大部分测试点的 $n$ 远小于上限。
3. **表存在 `list` 里而不是 `dict`**，省掉哈希开销。

> 如果这题改成「求 $n!$ 的**精确值**」，Python 的做法就是 `math.factorial(n)`，
> 一行搞定，而 C++ 选手要写高精度乘法。这就是 §1 说的优势面。

### BISHI33 Poi 的新加法（Easy Version）（简单）

> 定义二进制只进位加法 $f(x,y) = x + y - (x \oplus y)$，
> 求 $f(f(\cdots f(a_l, a_{l+1}) \cdots), a_r)$。
> $n \le 10^6$，$\sum n \le 10^6$，且保证 $l = 1, r = n$（Easy 版）。

先化简。$x + y = (x \oplus y) + 2(x \wedge y)$ 是二进制加法的基本恒等式
（异或是不进位加法，与运算左移一位是进位），所以：

$$f(x, y) = x + y - (x \oplus y) = 2(x \wedge y)$$

于是整个折叠就是：

$$f(f(a_1, a_2), a_3) = 2\big((2(a_1 \wedge a_2)) \wedge a_3\big)$$

注意 $2(a_1 \wedge a_2)$ 是**左移一位**，所以每折叠一次，前面的结果就整体左移一位再与下一个数取与。
逐位看：第 $k$ 位要在最终结果里为 1，需要一路对齐的那些位全为 1。

直接按定义迭代即可，$O(n)$：

```python
import sys


def main():
    data = sys.stdin.buffer.read().split()
    p = 0
    t = int(data[p]); p += 1                   # 数据组数
    out = []
    for _ in range(t):
        n, q = int(data[p]), int(data[p + 1]); p += 2   # 数列长度、询问个数
        a = data[p:p + n]; p += n              # 这 n 个 token 先不转 int，用到才转
        cur = int(a[0])                        # 折叠的初值就是第一个数
        for i in range(1, n):
            cur = (cur & int(a[i])) << 1      # f(x,y) = 2(x & y)，左移一位即乘 2
            if cur == 0:                       # 一旦归零，后面恒为零，提前退出
                break                          # 不退出的话 cur 会一路左移成百万位大整数
        # Easy 版保证 l=1, r=n，每个询问的答案都是同一个 cur
        for _ in range(q):
            p += 2                             # 询问行的 l、r 各占一个 token，读掉不用
            out.append(cur)
    sys.stdout.write("\n".join(map(str, out)) + "\n")


main()
```

**`if cur == 0: break` 这个剪枝很关键**：$a_i < 2^{60}$，
但每折叠一次结果就左移一位，$n$ 到 $10^6$ 时若不提前退出，`cur` 会变成百万位的大整数，
每次 `&` 都是 $O(d)$，总复杂度退化成 $O(n^2/30)$ 直接 TLE。
而实际上只要某一步与出 0，后面全是 0——这个剪枝把大整数膨胀彻底掐死。

> 这正是 §2 说的陷阱：**Python 的大整数不会溢出，但会悄悄变慢**。
> C++ 里 `uint64` 左移 60 次就自然归零了，Python 会老老实实地一直算下去。
> **凡是有左移的循环，都要问一句：结果会不会无限膨胀？**

---

### BM86 大数加法

给两个用字符串表示的非负整数，返回它们的和（同样用字符串表示）。
在 Python 里[BM86](../solutions/BM86.md)的正解是 `str(int(a) + int(b))` ——§1 那一节的整数没有上限，
一行结束，**而且不是投机取巧**：语言提供了这个能力，用它就是正确的工程选择。

值得说的是**这题在别的语言里为什么是道题**：C++ / Java 的定长整数会溢出，
必须手写按位相加与进位，也就是 §3 那份教学用模板里的 `add`。
换句话说，它属于「**语言差异造出来的题**」——同一道题在 Python 里没有难度，
在定长整数的语言里是必考题。

如果题面额外要求「不许调用大整数」，那就落回 §3 的手写模板：
两串补齐后从低位往高位逐位相加，进位只可能是 0 或 1，
循环结束后**别忘了最高位可能还有一个进位**。
把字符串反转后处理比每次算下标偏移更不容易错。

## 5　本章速查

| 场景 | 做法 |
| --- | --- |
| 大数加减乘除 | 直接用 `+ - * // %`，不需要模板 |
| 精确阶乘 | `math.factorial(n)` |
| 大数幂取模 | `pow(a, b, m)` |
| 大数开方 | `math.isqrt(n)`，不要用 `** 0.5` |
| 阶乘取模、多次询问 | 预处理前缀阶乘表，每步取模 |
| 循环里连乘 | 每步 `% MOD`，绝不最后才取模 |
| 有左移的循环 | 检查是否会无限膨胀，加提前退出 |
| 超大数转十进制 | $O(d^2)$，很贵；3.11+ 还有 4300 位限制 |
| 手写高精度 | 只在题目定义了自定义进位规则时才需要 |

---
id: string/hash
title: 字符串哈希
volume: 1
lang: py
---

# 第 36A 章　字符串哈希

<!-- CHAPTER-EXAMPLES -->
> **前置**：[哈希表](../ds/hash.md)、[字符串](../python/string.md)

把一个字符串压成一个整数，任意子串的比较就从 $O(n)$ 降到 $O(1)$。
和哈希表不同，这一套 Python 没有内置，必须自己写。

难点不在公式，在**参数**：base 写死会被卡，模数取小了会撞，自然溢出有必然反例。
所幸 Python 的原生大整数让这里比 C++ 更好办——单模 $2^{61}-1$ 一步到位，
不需要 `__int128`。冲突与取模的直觉和 [哈希表](../ds/hash.md) 是同一套。

---

## 1　原理

**目标**：把长度 $n$ 的字符串预处理成数组，之后**任意子串**的比较都是 $O(1)$。

**多项式哈希**：把字符串看成 $base$ 进制的数，对大素数 $M$ 取模：

$$H(s) = \left(\sum_{i=0}^{n-1} s_i \cdot base^{\,n-1-i}\right) \bmod M$$

前缀哈希 $h_i = H(s_0 \dots s_{i-1})$ 满足递推

$$h_0 = 0, \qquad h_{i+1} = (h_i \cdot base + s_i) \bmod M$$

于是子串 $s[l..r)$（左闭右开）的哈希是

$$H(s[l..r)) = \left(h_r - h_l \cdot base^{\,r-l}\right) \bmod M$$

这个式子和「$10$ 进制下从 $123456$ 里取出 $345$ 要减去 $12 \times 10^3$」是同一回事。

### 参数怎么选

| 参数 | 建议 | 理由 |
| --- | --- | --- |
| $base$ | **随机取 $[131, 10^9]$ 内的素数** | 固定 base 会被针对性卡 |
| $M$ | $2^{61}-1$（梅森素数）或 $10^9+7$ | 模数越大冲突概率越低 |
| 单模 vs 双模 | $M = 2^{61}-1$ 时单模足够；$M \approx 10^9$ 时**必须双模** | 见下面的生日悖论分析 |
| 自然溢出（$\bmod 2^{64}$） | ❌ **不要用** | 有经典的 Thue–Morse 反例可以必然卡掉 |

**冲突概率（生日悖论）**：比较 $q$ 个串两两之间是否相等，
出现假阳性的概率约 $\dfrac{q^2}{2M}$。

| $M$ | $q = 10^5$ | $q = 10^6$ |
| --- | --- | --- |
| $10^9+7$ | 约 $0.5\%$ | 约 **$40\%$** ← 危险 |
| $(10^9+7)^2$（双模） | $\approx 10^{-9}$ | $\approx 10^{-7}$ |
| $2^{61}-1$ | $\approx 2\times10^{-9}$ | $\approx 2\times10^{-7}$ |

> **Python 的优势**：模数取 $2^{61}-1$ 时，中间值 $h \cdot base$ 最大约 $2^{91}$，
> **C++ 需要 `__int128` 或手写快速乘**，Python 原生大整数直接算就行。
> 所以在 Python 里**单模 $2^{61}-1$ 是最优选择**：只算一遍，还比双 $10^9$ 更安全。

---

## 2　模板：字符串哈希类

```python
import random


class StringHash:
    """多项式前缀哈希，支持 O(1) 取任意子串哈希。

    模数取梅森素数 2^61 - 1：
      - 冲突概率约 q^2 / 2^62，10^6 次比较也只有 1e-7 量级；
      - Python 原生大整数直接算 h * base，不需要 C++ 的 __int128。
    base 随机化，防止被针对性构造数据卡。
    兼容 Python 3.9。
    """

    MOD = (1 << 61) - 1                  # 梅森素数；模数是素数，哈希值才在整个区间上均匀

    def __init__(self, s, base=None):
        """s 可以是 str 或 bytes。预处理 O(n)。"""
        if base is None:
            base = random.randrange(131, 1 << 40) | 1    # 或上 1 保证 base 为奇数
        self.base = base                 # 存下来：判回文时反串必须复用同一个 base
        M = self.MOD
        n = len(s)
        if isinstance(s, str):
            s = s.encode()               # 转 bytes 后 s[i] 直接是 0..255 的整数，省掉 ord()
        h = [0] * (n + 1)                # h[i] 是前 i 个字符的哈希；h[0] = 0 代表空串
        p = [1] * (n + 1)                # p[k] = base 的 k 次幂模 M，p[0] = 1
        for i in range(n):
            # 递推等价于在 base 进制数末尾追加一位：整体左移一位，再加上新字符
            h[i + 1] = (h[i] * base + s[i]) % M          # 下标错开一位，故写 h[i+1]
            p[i + 1] = p[i] * base % M   # 幂表顺手递推，查询时就不必再做快速幂
        self.h = h
        self.p = p
        self.n = n

    def get(self, l, r):
        """子串 s[l:r] 的哈希（左闭右开），O(1)。"""
        # h[r] 覆盖前 r 个字符，h[l] 覆盖前 l 个字符。两者位数差 r-l，
        # 所以 h[l] 要乘 base^(r-l) 才能和 h[r] 的高位对齐，相减剩下的正是 s[l:r]。
        # 同 10 进制下从 123456 里取出 345 要减去 12 * 10^3。
        # 差可能为负，Python 的 % 直接返回 [0, MOD) 内的结果，不必再补一个 MOD。
        return (self.h[r] - self.h[l] * self.p[r - l]) % self.MOD

    def equal(self, l1, r1, l2, r2):
        """判断两个子串是否相等，O(1)。"""
        if r1 - l1 != r2 - l2:           # 长度不等直接否掉：哈希只在等长时才有可比性
            return False
        return self.get(l1, r1) == self.get(l2, r2)
```

### 用法示例

```python
h = StringHash("abcabc")
h.equal(0, 3, 3, 6)         # True  —— "abc" == "abc"
h.get(1, 4)                 # "bca" 的哈希值
```

### 双模版本（模数只有 $10^9$ 级时用）

```python
class DoubleHash:
    """双模哈希：把两个模数下的哈希打包成一个元组/整数，
    冲突概率降到 (q^2) / (2 * M1 * M2)。

    Python 里通常不需要 —— 直接用 2^61-1 单模更快也更安全。
    这里给出是为了对照 C++ 的常见写法。
    """

    M1 = 1000000007                   # 两个模数必须互不相同，否则等同于单模
    M2 = 998244353

    def __init__(self, s, b1=131, b2=13331):
        if isinstance(s, str):
            s = s.encode()
        n = len(s)
        h1 = [0] * (n + 1); p1 = [1] * (n + 1)   # 第一套：前缀哈希 + 幂表
        h2 = [0] * (n + 1); p2 = [1] * (n + 1)   # 第二套：模数与 base 都换一组
        M1, M2 = self.M1, self.M2
        for i in range(n):                # 两套放在同一个循环里，字符串只遍历一遍
            h1[i + 1] = (h1[i] * b1 + s[i]) % M1
            p1[i + 1] = p1[i] * b1 % M1
            h2[i + 1] = (h2[i] * b2 + s[i]) % M2
            p2[i + 1] = p2[i] * b2 % M2
        self.h1, self.p1, self.h2, self.p2 = h1, p1, h2, p2

    def get(self, l, r):
        # 与单模同一个式子，只是在两个模数下各算一遍
        a = (self.h1[r] - self.h1[l] * self.p1[r - l]) % self.M1
        b = (self.h2[r] - self.h2[l] * self.p2[r - l]) % self.M2
        return a * self.M2 + b        # 打包成一个整数，方便丢进 set
        # b < M2 保证打包是单射：只有两个模下都相等，打包值才相等
```

---

## 3　典型用法

| 问题 | 做法 | 复杂度 |
| --- | --- | --- |
| 判两个子串是否相等 | 直接比哈希 | $O(1)$ |
| 统计有多少个**不同**的长度 $k$ 子串 | 全部子串哈希扔进 `set` | $O(n)$ |
| 判回文 | 正串哈希 == 反串对应位置哈希 | $O(1)$ |
| 求最长公共前缀 (LCP) | 二分长度 + 哈希比较 | $O(\log n)$ |
| 字符串匹配 | 枚举起点比哈希 | $O(n)$ |

> **但要注意**：
> - 字符串匹配有 $O(n)$ 且**无冲突风险**的 KMP（[字符串匹配KMP](../string/kmp.md)）；
> - 判回文有 $O(n)$ 的 Manacher（[回文](../string/manacher.md)）。
>
> **哈希的价值在于「通用」**：它能 $O(1)$ 比较任意两个子串，
> 这是 KMP 和 Manacher 都做不到的。所以哈希是**万金油**，不是最优解。

### 判回文的哈希写法

```python
def build_palindrome_checker(s):
    """返回一个 O(1) 判定 s[l:r] 是否回文的函数。"""
    fwd = StringHash(s)
    rev = StringHash(s[::-1], base=fwd.base)    # ★ 必须用同一个 base
    n = len(s)

    def is_pal(l, r):
        # 反转把下标 i 送到 n-1-i，所以 s[l:r] 的字符在反串里占 [n-r, n-l)。
        # 回文即「这一段正着读等于反着读」，比较两段哈希即可。
        return fwd.get(l, r) == rev.get(n - r, n - l)

    return is_pal
```

> **陷阱**：正串和反串**必须用同一个 base 和同一个模数**，否则完全没有可比性。
> 上面 `base=fwd.base` 那一行是全部关键。

---

## 4　例题

<!-- CHAPTER-EXAMPLE-TABLE -->

### BISHI7 字符串哈希（简单）

> 给定 $N \le 10^4$ 个字符串（仅含数字和大小写字母，$1 \le |s_i| \le 1500$），
> 求其中**不同字符串的个数**。
> 题面见 [原题](https://www.nowcoder.com/practice/dadbd37fee7c43f0ae407db11b16b4bf)。

题目名叫「字符串哈希」，C++ 的标准做法是给每个串算多项式哈希再去重，
避免 $O(N^2 |s|)$ 的两两比较。

**但在 Python 里这题是一行**：

```python
import sys


def main():
    data = sys.stdin.buffer.read().split()   # bytes 本身可哈希，全程不 decode
    n = int(data[0])
    # 只取前 n 个 token：输入尾部若有多余空行或脏数据，切片会把它们挡在外面
    sys.stdout.write(str(len(set(data[1:1 + n]))) + "\n")


main()
```

因为 `bytes` 本身就是可哈希的，`set` 内部就是哈希表，
而且哈希计算是 **C 实现的 SipHash**——比手写多项式哈希又快、又不会被卡冲突
（而且冲突后 `set` 会真的做一次字节比较，**结果永远正确**，
不像多项式哈希有假阳性风险）。

复杂度 $O(\sum |s_i|)$，总字符量最多 $1.5\times10^7$，
比两两比较的 $O(N^2|s|) = 1.5\times10^{11}$ 快四个数量级。

**四个坑**：

1. **区分大小写**，不能 `lower()`：样例里 `Hello` / `hello` / `HELLO` 算 3 个不同串；
2. 串里只有数字和字母（无空格），所以可以放心 `split()` 按空白切 token；
3. 只取前 $N$ 个 token，防止输入尾部有多余空行 / 脏数据；
4. **直接对 `bytes` 去重**，省掉 $10^4$ 次 `decode()`。

题解见 [`solutions/nowcoder/BISHI7/sol.py`](../solutions/BISHI7.md)。

> **教学要点**：这题揭示了一条通用原则——
> **凡是「Python 内置类型已经可哈希」的对象，就不要自己写哈希函数。**
> 手写多项式哈希只在需要**「子串」哈希**（$O(1)$ 取任意区间）时才有价值。

---

## 5　本章速查

| 要点 | 结论 |
| --- | --- |
| 字符串去重 | **直接 `set(bytes)`**，不要手写多项式哈希 |
| 手写哈希的价值 | 只在需要 **$O(1)$ 取子串哈希**时 |
| 模数选择 | Python 用 **$2^{61}-1$ 单模**（原生大整数，无需 `__int128`） |
| base | **随机化**，别写死 131 |
| 自然溢出 $2^{64}$ | ❌ 有 Thue–Morse 反例，必被卡 |
| 双模 | $M \approx 10^9$ 时必须；用 $2^{61}-1$ 时不必 |
| 正串+反串判回文 | **必须同 base 同模数** |
| 冲突概率 | 约 $q^2 / (2M)$（生日悖论） |

| 子串哈希公式 | |
| --- | --- |
| 前缀递推 | $h_{i+1} = (h_i \cdot base + s_i) \bmod M$ |
| 区间取值 | $H(s[l..r)) = (h_r - h_l \cdot base^{\,r-l}) \bmod M$ |

哈希表本身的性质（哪些键安全、什么时候改用数组）在
[哈希表](../ds/hash.md) 章末。

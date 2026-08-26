---
id: math/number/euler
title: 欧拉函数与欧拉降幂
volume: 2
lang: py
---

# 第 82 章　欧拉函数与欧拉降幂

<!-- CHAPTER-EXAMPLES -->
> **前置**：[数论基础](basic.md)、[快速幂与逆元](inverse.md)

欧拉函数是**费马小定理走向一般模数**的那把钥匙。
掌握它之后，「模数不是质数怎么办」和「指数是个天文数字怎么办」这两类题就有了统一答案。

---

## 1　定义与公式

> **定义**：$\varphi(n)$ 表示 $1, 2, \ldots, n$ 中与 $n$ **互质**的数的个数。

约定 $\varphi(1) = 1$（$1$ 与 $1$ 互质）。

前几项：

| $n$ | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 12 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| $\varphi(n)$ | 1 | 1 | 2 | 2 | 4 | 2 | 6 | 4 | 6 | 4 | 4 |

### 公式

设 $n = p_1^{a_1} p_2^{a_2} \cdots p_k^{a_k}$，则

$$\varphi(n) = n \prod_{i=1}^{k}\left(1 - \frac{1}{p_i}\right) = \prod_{i=1}^{k} p_i^{a_i - 1}(p_i - 1)$$

（后一种写法的好处是**全程整数运算**。）

**证明一（容斥）**：设 $A_i$ 是 $[1,n]$ 中 $p_i$ 的倍数构成的集合，$|A_i| = n/p_i$。
与 $n$ 互质就是不属于任何 $A_i$。由容斥原理

$$\varphi(n) = n - \sum |A_i| + \sum|A_i \cap A_j| - \cdots
= n\left(1 - \sum\frac{1}{p_i} + \sum\frac{1}{p_ip_j} - \cdots\right)
= n\prod_{i}\left(1-\frac1{p_i}\right) \qquad \square$$

**证明二（积性 + 质数幂）**：

- 先算 $\varphi(p^q)$。$[1, p^q]$ 中与 $p^q$ **不**互质的数恰是 $p$ 的倍数，共 $p^{q-1}$ 个。
  所以 $\varphi(p^q) = p^q - p^{q-1} = p^{q-1}(p-1)$。
  （这正是「关键问题是求出 $\varphi(p^q)$ 的值」那类题的答案。）
- 再证 $\varphi$ 是**积性函数**：$\gcd(a,b)=1$ 时 $\varphi(ab)=\varphi(a)\varphi(b)$。
  由中国剩余定理，映射 $x \mapsto (x \bmod a,\ x \bmod b)$ 是
  $\mathbb{Z}_{ab} \to \mathbb{Z}_a \times \mathbb{Z}_b$ 的双射，
  且 $\gcd(x,ab)=1 \iff \gcd(x,a)=1$ 且 $\gcd(x,b)=1$。
  所以两边的互质元素个数相等。$\square$
- 两条合起来，对 $n = \prod p_i^{a_i}$ 逐个相乘即得公式。

### 积性函数

> **定义**：对于函数 $f$，如果对任意 $\gcd(a,b)=1$ 有 $f(ab)=f(a)f(b)$，
> 则 $f$ 是**积性函数**。若对**任意** $a,b$ 都成立，则称**完全积性**。

常见的积性函数：

| 函数 | 含义 | $f(p^a)$ |
| --- | --- | --- |
| $\varphi(n)$ | 欧拉函数 | $p^{a-1}(p-1)$ |
| $\mu(n)$ | 莫比乌斯函数（[整除分块与数论进阶](sqrt-decomposition.md)） | $a=1$ 时 $-1$；$a\ge2$ 时 $0$ |
| $d(n)$ | 约数个数 | $a+1$ |
| $\sigma(n)$ | 约数和 | $\frac{p^{a+1}-1}{p-1}$ |
| $\operatorname{id}(n)=n$、$\mathbf{1}(n)=1$ | 完全积性 | — |

**积性函数的通用算法**：

> 对于所有质数的幂, 算出函数值。将每个数分解成若干质数的幂的乘积,
> 将每个质数的幂的函数值乘起来即可。需要预处理每个数的最小质因子和所含最小质因子的最高幂。

---

## 2　求单个 $\varphi(n)$：试除法

按公式，边分解质因数边乘：

### 模板一：试除法求欧拉函数

```python
# [片段] 模板：试除法求单个 φ(n)，O(sqrt n)
def phi(n):
    """欧拉函数，试除法。n = 1 时返回 1。"""
    res = n
    p = 2
    while p * p <= n:
        if n % p == 0:
            res = res // p * (p - 1)     # ★ 先除后乘，保证整除、也不膨胀
            while n % p == 0:            # 把 p 除干净
                n //= p
        p += 1 if p == 2 else 2          # 2 之后只试奇数
    if n > 1:                            # ★ 剩下的大质因子
        res = res // n * (n - 1)
    return res
```

**三个必须注意的点**：

1. **`res = res // p * (p - 1)` 先除后乘**。写成 `res * (p-1) // p` 在中间步骤会
   出现非整除（虽然 Python 的 `//` 最终结果一样，但先除后乘的中间量更小、
   翻译回 C++ 也不会溢出）。这里 $p \mid \text{res}$ 是有保证的，因为 $p \mid n$ 且 res 是 $n$ 的因子倍数；
2. **每个质因子只贡献一次 $(p-1)/p$**，重数不影响——公式里就是 $\prod(1-1/p_i)$，
   所以找到 $p$ 后要 `while` 除干净再继续；
3. **最后那句 `if n > 1` 不能少**。$n$ 是质数（如 $999999937$）时循环里进不去，
   全靠这一句，否则会输出 $n$ 而不是 $n-1$。

### 常数优化：只用质数试除

$T$ 组询问时，「$p$ 从 2 逐个枚举到 $\sqrt n$」是 $O(T\sqrt n)$。
$x \le 10^9$ 时 $\sqrt x = 31623$，$T = 5000$ 就是 $1.6\times10^8$ 次 Python 取模——**太慢**。

**先用埃氏筛把 $31623$ 以内的 3401 个质数筛出来，只拿质数去试除**，
最坏 $5000 \times 3401 \approx 1.7\times10^7$ 次，降到原来的 $1/10$。
筛表本身用 `bytearray` 切片赋值，几乎不耗时（见 [数论基础](basic.md) 模板二）。

---

## 3　求 $\varphi(1..n)$：线性筛

线性筛求 $arphi$ 的 C++ 写法：

```cpp
void sieve() {
    phi[1] = 1;
    for (int i = 2; i <= n; i++) {
        if (!flag[i]) prime[++tot] = i, phi[i] = i - 1;
        for (int j = 1; j <= tot && i * prime[j] <= n; j++) {
            flag[i * prime[j]] = true;
            if (i % prime[j]==0) { phi[i * prime[j]] = phi[i] * prime[j]; break; }
            else phi[i * prime[j]] = phi[i] * (prime[j] - 1);
        }
    }
}
```

三个分支对应三条事实：

| 情形 | 递推 | 依据 |
| --- | --- | --- |
| $i$ 是质数 | $\varphi(i) = i-1$ | 质数与前面所有数互质 |
| $p \mid i$ | $\varphi(ip) = \varphi(i)\cdot p$ | $ip$ 与 $i$ 的质因子**集合相同**，公式里只有前面的 $n$ 乘了 $p$ |
| $p \nmid i$ | $\varphi(ip) = \varphi(i)(p-1)$ | $\gcd(i,p)=1$，用积性 + $\varphi(p)=p-1$ |

### 模板二：线性筛求欧拉函数表

```python
# [片段] 模板：线性筛，同时得到素数表与 φ 表，O(n)
def sieve_phi(n):
    """返回 (primes, phi)，phi[i] = φ(i)，i = 0..n。"""
    phi = list(range(n + 1))
    phi[0] = 0
    primes = []
    is_comp = bytearray(n + 1)
    for i in range(2, n + 1):
        if not is_comp[i]:
            primes.append(i)
            phi[i] = i - 1
        for p in primes:
            v = i * p
            if v > n:
                break
            is_comp[v] = 1
            if i % p == 0:
                phi[v] = phi[i] * p      # p 已是 i 的质因子
                break                    # ★ 这个 break 保证线性
            phi[v] = phi[i] * (p - 1)
    return primes, phi
```

> **Python 的现实评估**：这是**纯 Python 的双重循环**，
> $n = 10^6$ 约 0.9 秒，$n = 2\times10^6$ 约 2 秒，再大就不实用了。
> 对比 [数论基础](basic.md) 的 `bytearray` 埃氏筛（$10^6$ 只要 0.002 秒），
> 差了两个数量级——但埃氏筛给不出 $\varphi$，**这个代价是不得不付的**。
>
> **替代方案**：如果只需要 $\varphi$ 的**前缀和**或者只查询少量的 $\varphi(x)$，
> 用试除法逐个算往往更划算（$T$ 次 $O(\sqrt x)$ vs 一次 $O(n)$ 但常数巨大）。
> 判断标准：**$T \cdot \sqrt{V}$ 和 $30 V$ 谁小**（$30$ 是线性筛在 Python 里的常数）。

**用埃氏筛思路求 $\varphi$ 表的折中方案**（$O(n\log\log n)$ 但内层能部分下沉）：

```python
# [片段] 折中：埃氏筛式求 φ 表，外层 Python、内层是 range 步长循环
def phi_table_eratos(n):
    phi = list(range(n + 1))
    for i in range(2, n + 1):
        if phi[i] == i:                  # i 是质数（还没被任何质因子改过）
            for j in range(i, n + 1, i):
                phi[j] -= phi[j] // i    # 乘上 (1 - 1/i)
    return phi
```

内层循环总次数仍是 $O(n\log\log n)$ 次 Python 迭代，$n=10^6$ 约 1.8 秒——
**比线性筛还慢**（线性筛只有 $n$ 次）。所以在 Python 里，
**求 $\varphi$ 表就老老实实用线性筛，别指望 `bytearray` 那种魔法**。

---

## 4　欧拉函数的性质

| 性质 | 内容 | 说明 |
| --- | --- | --- |
| 积性 | $\gcd(a,b)=1 \Rightarrow \varphi(ab)=\varphi(a)\varphi(b)$ | 见 §1 |
| 质数 | $\varphi(p)=p-1$ | |
| 质数幂 | $\varphi(p^a)=p^{a-1}(p-1)$ | |
| **约数和** | $\sum_{d \mid n}\varphi(d) = n$ | 见下方证明 |
| 偶性 | $n > 2 \Rightarrow \varphi(n)$ 是偶数 | 见下方证明 |
| 减半 | $n$ 为偶数 $\Rightarrow \varphi(n) \le n/2$ | 由公式含因子 $(1-1/2)$ |
| 与 $n$ 的关系 | $\varphi(n) < n$（$n>1$） | |

**证明（$\sum_{d\mid n}\varphi(d)=n$）**：把 $\{1,2,\ldots,n\}$ 按 $\gcd(k,n)$ 的值分类。
$\gcd(k,n)=d$ 的 $k$ 可以写成 $k=dm$，条件变成 $\gcd(m, n/d)=1$ 且 $1\le m \le n/d$，
这样的 $m$ 恰有 $\varphi(n/d)$ 个。于是
$$n = \sum_{d\mid n}\varphi(n/d) = \sum_{d\mid n}\varphi(d) \qquad \square$$

（这条式子常用来化简 $\sum_a\sum_b \gcd(a,b)$，见
[整除分块与数论进阶](sqrt-decomposition.md)。）

**证明（$n>2$ 时 $\varphi(n)$ 是偶数）**：
若 $n$ 有奇质因子 $p$，则 $\varphi$ 的公式里含因子 $(p-1)$，是偶数；
若 $n = 2^a$（$a\ge2$），则 $\varphi(n)=2^{a-1}$ 也是偶数。$\square$

**这条性质是欧拉降幂能收敛的关键**，见 §6。

---

## 5　欧拉定理

> **定理（Euler）**：若 $\gcd(a, m) = 1$，则 $a^{\varphi(m)} \equiv 1 \pmod m$。

**证明**（把费马小定理的证明照搬到简化剩余系上）：
设 $r_1, r_2, \ldots, r_{\varphi(m)}$ 是模 $m$ 的**简化剩余系**
（即 $[1,m]$ 中与 $m$ 互质的全部数）。因为 $\gcd(a,m)=1$：

- $\gcd(ar_i, m)=1$，所以 $ar_i$ 仍落在简化剩余系里；
- 由消去律，$ar_i \equiv ar_j \Rightarrow r_i \equiv r_j$，所以 $ar_1,\ldots,ar_{\varphi(m)}$ 两两不同余。

于是 $\{ar_i\}$ 是 $\{r_i\}$ 的一个排列。两边取积：

$$a^{\varphi(m)}\prod r_i \equiv \prod r_i \pmod m$$

$\prod r_i$ 与 $m$ 互质，消去即得。$\square$

**费马小定理是它的特例**：$m = P$ 为质数时 $\varphi(P) = P-1$。

**推论（一般模数求逆元）**：$\gcd(a,m)=1$ 时

$$a^{-1} \equiv a^{\varphi(m)-1} \pmod m$$

> **但实战别用这条求逆元**：算 $\varphi(m)$ 本身要 $O(\sqrt m)$，
> 比扩展欧几里得的 $O(\log m)$ 慢得多。Python 直接 `pow(a, -1, m)` 就好。
> 见 [快速幂与逆元](inverse.md)。

---

## 6　扩展欧拉定理（欧拉降幂）

欧拉定理要求 $\gcd(a,m)=1$。当这个条件不成立时，有更强的版本：

> **定理（扩展欧拉定理 / 欧拉降幂）**：对**任意**正整数 $a, m$ 和非负整数 $b$，
> $$a^{b} \equiv \begin{cases}
> a^{b} & b < \varphi(m) \\[2pt]
> a^{\,b \bmod \varphi(m)\ +\ \varphi(m)} & b \ge \varphi(m)
> \end{cases} \pmod m$$

**关键点**：第二式**不要求 $\gcd(a,m)=1$**，这正是「扩展」相对费马小定理的价值。

> **证明思路**：把 $a$ 的质因子分成「整除 $m$ 的」和「与 $m$ 互质的」两部分，
> 由中国剩余定理把 $m$ 拆成 $m = m_1 m_2$，$m_1$ 只含 $a$ 的质因子、$\gcd(a,m_2)=1$。
> - 模 $m_2$ 部分：欧拉定理直接给出 $a^{\varphi(m_2)}\equiv1$，
>   而 $\varphi(m_2) \mid \varphi(m)$，所以指数加减 $\varphi(m)$ 不改变结果；
> - 模 $m_1$ 部分：$m_1 \le m$ 且 $m_1$ 的每个质因子都整除 $a$，
>   可以证明 $m_1 \le 2^{\varphi(m)}$，故当指数 $\ge \varphi(m)$ 时
>   $a^{b} \equiv 0 \equiv a^{b+\varphi(m)} \pmod{m_1}$；
>
> 两部分都成立，由 CRT 合并即得。$\square$

**「$b \ge \varphi(m)$」这个条件绝不能省**：

```python
# ❌ 无脑 +φ(m)
pow(2, 1 % 4 + 4, 5)      # 2^5 mod 5 = 2
# ✅ 指数 1 < φ(5)=4，应该直接算
pow(2, 1, 5)              # 2^1 mod 5 = 2   —— 这次碰巧一样
pow(3, 2 % 4 + 4, 10)     # 3^6 mod 10 = 9
pow(3, 2, 10)             # 3^2 mod 10 = 9  —— 也一样
# 真正会错的例子：
pow(2, 2 % 4 + 4, 12)     # 2^6 mod 12 = 4
pow(2, 2, 12)             # 2^2 mod 12 = 4  ← 巧合
pow(2, 1 % 4 + 4, 12)     # 2^5 mod 12 = 8
pow(2, 1, 12)             # 2^1 mod 12 = 2  ← ★ 不一样！
```

$m=12$、$\varphi(12)=4$、$b=1<4$ 时无脑降幂会得到 8 而正确答案是 2。
**小指数必须原样算。**

### $\varphi$ 迭代的收敛速度

处理**幂塔** $a_1^{a_2^{a_3^{\cdots}}}$ 时要一层层降幂，模数依次变成
$m, \varphi(m), \varphi(\varphi(m)), \ldots$。这条链有多长？

> **定理**：$\varphi$ 迭代 $O(\log m)$ 次后必然落到 1。
>
> **证明**：
> - $m$ 为偶数：$\varphi(m) \le m/2$（公式含因子 $\frac12$）；
> - $m$ 为大于 2 的奇数：由 §4，$\varphi(m)$ 是**偶数**，于是下一步减半。
>
> 所以**每两步至少减半**，链长 $\le 2\log_2 m$。$\square$

$m = 10^9+7$ 时链长约 $60$ 层。**这个上界与幂塔的高度无关**——
哪怕塔高 $10^6$，真正需要递归的也只有 60 层，因为模数落到 1 之后一切都是 0。

### 模板三：欧拉降幂（幂塔求值）

```python
# [片段] 模板：幂塔 a^(a^(a^...)) mod m 的欧拉降幂框架
def phi(x):
    res, p = x, 2
    while p * p <= x:
        if x % p == 0:
            res = res // p * (p - 1)
            while x % p == 0:
                x //= p
        p += 1 if p == 2 else 2
    if x > 1:
        res = res // x * (x - 1)
    return res


def power_tower(a, h, m):
    """高度为 h 的幂塔 a^(a^(...^a)) mod m。递归深度只有 O(log m)。"""
    if m == 1:
        return 0                       # ★ 模 1 恒为 0，同时终止 φ 链
    if h == 0:
        return 1 % m
    pm = phi(m)
    e = power_tower(a, h - 1, pm)      # 上层塔 mod φ(m)
    # 判断真实指数是否 >= φ(m)：塔高 >= 2 且 a >= 2 时几乎必然成立
    if a >= 2 and h >= 2:
        e += pm                        # ★ 只有指数 >= φ(m) 才做这个修正
    return pow(a % m, e, m)
```

> **「指数是否 $\ge \varphi(m)$」怎么判？** 不能真的把塔算出来（它是天文数字）。
> 实战有两条路：
> 1. **硬编码小情形**：塔的前几层精确算，超过某个高度必然大于任何模数（BISHI75 用的就是这个）；
> 2. **带标记的递归**：让递归函数同时返回「值 mod m」和「真实值是否 $\ge m$」两个信息。

---

## 7　例题

<!-- CHAPTER-EXAMPLE-TABLE -->

### BISHI73 【模板】欧拉函数计算Ⅰ ‖ 朴素求值：试除法（中等）

> $T \le 5\times10^3$ 组，每组给 $1 \le x \le 10^9$，输出 $\varphi(x)$。
> 题面见 [原题](https://www.nowcoder.com/practice/6a22f91ad3904c6cbd624ae5ff6a4eac)。

标准试除法，考点全在**常数**上。

| 做法 | 循环次数 | 判断 |
| --- | --- | --- |
| $p$ 从 2 逐个枚举到 $\sqrt x$ | $5\times10^3 \times 3.2\times10^4 = 1.6\times10^8$ | ❌ Python 下太慢 |
| **先筛出 $\sqrt{10^9}$ 以内的质数，只用质数试除** | $5\times10^3 \times 3401 \approx 1.7\times10^7$ | ✅ |

$31623$ 以内有 3401 个质数，密度约 $1/10$，所以循环次数正好降一个数量级。
而且大多数 $x$ 会被小质因子迅速削小，`p * p > x` 的提前退出让实际次数远低于最坏值。

```python
import math
import sys


def build_primes(limit):
    """埃氏筛：bytearray + 切片赋值，内层循环走 C。"""
    sieve = bytearray([1]) * (limit + 1)
    sieve[0:2] = b"\x00\x00"
    for i in range(2, math.isqrt(limit) + 1):
        if sieve[i]:
            sieve[i * i::i] = bytearray(len(range(i * i, limit + 1, i)))
    return [i for i in range(2, limit + 1) if sieve[i]]


def main():
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    primes = build_primes(31623)          # sqrt(1e9) 上取整
    out = []
    ap = out.append
    for tok in data[1:t + 1]:
        x = int(tok)
        res = x
        for p in primes:
            if p * p > x:                 # ★ x 随除法缩小，上界自动收紧
                break
            if x % p == 0:
                res = res // p * (p - 1)  # 先除后乘，保证整除
                while x % p == 0:
                    x //= p
        if x > 1:                         # ★ 剩下的大质因子
            res = res // x * (x - 1)
        ap(str(res))
    sys.stdout.write("\n".join(out) + "\n")


main()
```

**四个坑**：

1. $\varphi(1) = 1$。公式里没有质因子，`res` 保持 1，天然正确（样例第一行）；
2. **最后的 `if x > 1`**：$x = 999999937$ 是质数，漏了这步会输出 $999999937$
   而不是正确的 $999999936$（样例第四行专门在考这个）；
3. 循环条件用 `p * p > x` 而不是预先算死 `isqrt(x)`——因为 $x$ 在缩小；
4. `res = res // p * (p-1)` **先除后乘**。

**验算样例**：$\varphi(10^9) = \varphi(2^9 5^9) = 10^9 \cdot \frac12 \cdot \frac45 = 4\times10^8$ ✓

题解见 [`solutions/nowcoder/BISHI73/sol.py`](../../solutions/BISHI73.md)。

### BISHI75 阶幂（中等）

> 定义 $fp(n) = 1$（$n \le 1$）、$fp(n) = n^{fp(n-1)}$（$n \ge 2$）。
> 给定 $1 \le n \le 10^6$，求 $fp(n) \bmod (10^9+7)$。
> 题面见 [原题](https://www.nowcoder.com/practice/da7a14c1a58b48bd80e63771b82e50c5)。

**这是欧拉降幂的教科书例题**：一个高度达 $10^6$ 的幂塔。

按扩展欧拉定理递归：

$$\operatorname{calc}(n, m) = n^{\operatorname{calc}(n-1,\ \varphi(m))} \bmod m$$

模数每递归一层就变成 $\varphi(m)$。由 §6 的收敛性，
$m = 10^9+7$ 时约 60 层就落到 1，**递归深度与 $n$ 无关**。

**「指数是否 $\ge \varphi(m)$」的判定**：$fp$ 增长得极快——

$$fp(1)=1,\quad fp(2)=2,\quad fp(3)=3^2=9,\quad fp(4)=4^9=262144,\quad fp(5)=5^{262144}$$

从 $n \ge 5$ 起 $fp(n)$ 已经碾压任何 $m \le 10^9+7$，所以只需**硬编码前 4 项**做比较。

```python
import sys

MOD = 1000000007
# fp(1..4) 的精确值；n >= 5 时 fp(n) >= 5^262144，比任何模数都大得多
SMALL = (1, 1, 2, 9, 262144)


def phi(x):
    """试除法求欧拉函数。x <= 1e9+7，只需除到 sqrt(x)。"""
    res = x
    p = 2
    while p * p <= x:
        if x % p == 0:
            res = res // p * (p - 1)
            while x % p == 0:
                x //= p
        p += 1 if p == 2 else 2
    if x > 1:
        res = res // x * (x - 1)
    return res


def ge(n, m):
    """判断 fp(n) >= m，不必真的算出 fp(n)。"""
    if n <= 4:
        return SMALL[max(n, 0)] >= m
    return True                     # fp(5) = 5^262144，碾压一切 m


def calc(n, m):
    """fp(n) mod m。"""
    if m == 1:
        return 0                    # ★ 模 1 恒为 0，同时终止 φ 链
    if n <= 1:
        return 1                    # fp(0)=fp(1)=1，且此时 m >= 2
    pm = phi(m)
    e = calc(n - 1, pm)             # e = fp(n-1) mod φ(m)
    if ge(n - 1, pm):               # ★ 指数 >= φ(m) 才做「+φ(m)」的降幂修正
        e += pm
    return pow(n % m, e, m)


n = int(sys.stdin.buffer.read().split()[0])
sys.stdout.write(str(calc(n, MOD)) + "\n")
```

**四个坑**：

1. **降幂条件必须是「指数 $\ge \varphi(m)$」才加回 $\varphi(m)$**。
   小于时直接用原指数——无脑 $+\varphi(m)$ 在 $n=2,3$ 这类小情形会算错；
2. **$m$ 递归到 1 时立刻返回 0**，否则 $\varphi(1)=1$ 会死循环；
3. 底数要先 `n % m` 再进 `pow`（$n$ 可能远大于 $m$）；
4. $n \le 1$ 时 $fp(n)=1$（样例 1）。

**复杂度**：递归层数 $\approx \min(n, 60)$，每层一次 $O(\sqrt m)$ 的 $\varphi$ 和一次 C 层 `pow`，
总计 $O(\log m \cdot \sqrt m)$，实测毫秒级。

> **为什么不能从 $n=1$ 正着递推？**
> 因为每一层的**指数要模的数都不一样**（$\varphi$ 链上不同的模数），
> 正推时无从知道下一层需要的是模哪个数的结果。必须从最外层往里剥。

题解见 [`solutions/nowcoder/BISHI75/sol.py`](../../solutions/BISHI75.md)。

---

## 8　本章速查

### 公式

| 名称 | 内容 |
| --- | --- |
| 定义 | $\varphi(n) = \#\{k \in [1,n] : \gcd(k,n)=1\}$，$\varphi(1)=1$ |
| 公式 | $\varphi(n)=n\prod(1-1/p_i)=\prod p_i^{a_i-1}(p_i-1)$ |
| 质数幂 | $\varphi(p^a)=p^a-p^{a-1}$ |
| 积性 | $\gcd(a,b)=1 \Rightarrow \varphi(ab)=\varphi(a)\varphi(b)$ |
| 约数和 | $\sum_{d\mid n}\varphi(d)=n$ |
| 偶性 | $n>2 \Rightarrow 2 \mid \varphi(n)$ |
| 欧拉定理 | $\gcd(a,m)=1 \Rightarrow a^{\varphi(m)}\equiv1\pmod m$ |
| 费马小定理 | 上式在 $m=P$ 质数时的特例 |
| **欧拉降幂** | $b \ge \varphi(m)$ 时 $a^b \equiv a^{b \bmod \varphi(m)+\varphi(m)}$，**不要求互质** |
| $\varphi$ 链 | 迭代 $O(\log m)$ 次落到 1（每两步至少减半） |

### 求法选择

| 需求 | 做法 | 复杂度 | Python 上限 |
| --- | --- | --- | --- |
| 单个 $\varphi(x)$，$x \le 10^{12}$ | 试除法 | $O(\sqrt x)$ | 单次 $\sim0.3$ s |
| $T$ 组单点查询 | **筛出 $\sqrt V$ 内的质数再试除** | $O(T\pi(\sqrt V))$ | $T\le10^4$ |
| $\varphi(1..n)$ 全表 | 线性筛 | $O(n)$ 但常数大 | $n \le 2\times10^6$ |
| 幂塔 / 巨大指数 | 欧拉降幂递归 | $O(\log m \sqrt m)$ | 无压力 |

### 陷阱清单

| 陷阱 | 后果 |
| --- | --- |
| 试除后忘了 `if n > 1` | 质数的 $\varphi$ 直接算错 |
| `res * (p-1) // p` 而非先除后乘 | 中间量膨胀（C++ 里直接溢出） |
| 降幂时无脑 $+\varphi(m)$ | 小指数情形算错（$2^1 \bmod 12$：得 8 而非 2） |
| $\varphi$ 链没在 $m=1$ 处终止 | 死循环 |
| 用 $a^{\varphi(m)-1}$ 求逆元 | 比 exgcd 慢得多，且要先分解 $m$ |
| 在 Python 里指望线性筛跑 $10^7$ | 纯 Python 双重循环，必然 TLE |

### 看到什么 → 想到欧拉函数

| 题面特征 | 想到 |
| --- | --- |
| 「与 $n$ 互质的数的个数」 | $\varphi(n)$ 定义 |
| 「既约分数 / 可见格点」 | $\varphi$ 或莫比乌斯（[整除分块与数论进阶](sqrt-decomposition.md)） |
| 指数是幂塔 / 指数本身要取模 | **欧拉降幂**，注意 $b\ge\varphi(m)$ 的条件 |
| 模数不是质数但要求逆元 | $\gcd=1$ 时用 exgcd（[快速幂与逆元](inverse.md)） |
| $\sum_{i}\gcd(i,n)$ | $\sum_{d\mid n} d\,\varphi(n/d)$ |
| $\sum_{d\mid n}\varphi(d)$ | 直接等于 $n$ |

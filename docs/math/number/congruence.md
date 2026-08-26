---
id: math/number/congruence
title: 同余方程组与离散对数
volume: 2
lang: py
---

# 第 114 章　同余方程组与离散对数

<!-- CHAPTER-EXAMPLES -->
> **前置**：[数论基础](basic.md)、[快速幂与逆元](inverse.md)

## 1　这一章为什么存在

竞赛数论里有三个知识点，是「基础数论」讲完之后的自然延伸：

| 知识点 | 解决什么问题 |
| --- | --- |
| **CRT**（Chinese remainder theorem，中国剩余定理） | 已知 $x \bmod p_i$，还原 $x$ |
| **BSGS**（baby-step giant-step，大步小步算法） | 已知 $a^x \equiv b$，求 $x$（**离散对数**） |
| **高斯消元** | 解线性方程组 |

三者的共同点：**都是「已知运算结果，反推未知数」**，
是 [数论基础](basic.md)「已知未知数求结果」的逆问题。

配套题单里没有直接考它们的题。最接近的是 BISHI74（**非质模数**下的逆元）——
它用的扩展欧几里得正是 CRT 的核心零件，把它讲透，CRT 就只差临门一脚。

这一章的定位：**把这三件工具补齐，并说清楚 Python 在这里的独特优势**——
Python 的 `pow(a, -1, m)` 内置扩展欧几里得，大整数不会溢出，
**CRT 和高斯消元在 Python 里比在 C++ 里好写得多**。

---

## 2　回顾：扩展欧几里得与逆元

CRT 的每一步都要求逆元，所以先把这块钉牢。

**裴蜀定理**：$ax + by = \gcd(a,b)$ 一定有整数解。
**扩展欧几里得**在求 $\gcd$ 的同时求出这组 $(x, y)$。

```python
# [片段]
def exgcd(a, b):
    """迭代版扩展欧几里得。返回 (g, x, y) 满足 a*x + b*y = g = gcd(a, b)。

    迭代而非递归：竞赛中 T 可达 1e4，递归的函数调用开销明显，且没有必要。
    """
    # 循环不变量：old_r = old_s*a + old_t*b，r = s*a + t*b，两式始终成立
    old_r, r = a, b                          # 余数列，就是普通辗转相除的那一对
    old_s, s = 1, 0                          # a 的系数列，初值对应 a = 1*a + 0*b
    old_t, t = 0, 1                          # b 的系数列，初值对应 b = 0*a + 1*b
    while r:
        q = old_r // r                       # 商，三组变量共用同一个 q
        old_r, r = r, old_r - q * r          # 余数按辗转相除推进
        old_s, s = s, old_s - q * s          # 系数跟着做同样的线性组合
        old_t, t = t, old_t - q * t
    return old_r, old_s, old_t               # r 归零时 old_r 就是 gcd，系数随之成立
```

**逆元存在的充要条件**：$\gcd(a, m) = 1$。
因为 $ax \equiv 1 \pmod m \iff ax + my = 1$，左边恒是 $\gcd(a,m)$ 的倍数。

| 求逆元的方法 | 条件 | 复杂度 | Python 写法 |
| --- | --- | --- | --- |
| 费马小定理 $a^{p-2}$ | $p$ **必须是质数** | $O(\log p)$ | `pow(a, p - 2, p)` |
| **扩展欧几里得** | 只需 $\gcd(a,m)=1$ | $O(\log m)$ | **`pow(a, -1, m)`**（3.8+） |
| 线性递推 $1..n$ 的逆元 | $p$ 质数 | $O(n)$ | 见 [快速幂与逆元](inverse.md) |

> **`pow(a, -1, m)` 是 Python 3.8 引入的**，内部就是扩展欧几里得，
> 逆元不存在时抛 `ValueError`。**牛客的 Python 3.9 完全支持**。
> 竞赛中直接用它，比手写快也不会写错。
> 手写版只在需要**同时拿到 $\gcd$** 或做扩展 CRT 的中间量时才有用。

---

## 3　中国剩余定理（模数两两互质）

**问题**：

> $a \bmod p_i = b_i$，$p_i$ 为**互质**的数，已知 $p_i$ 和 $b_i$，
> 求 $b = a \bmod (p_1 p_2 \cdots p_n)$ 的值。

**构造**：

> 设 $M_i = \dfrac{p_1 p_2 \cdots p_n}{p_i}$，$m_i = M_i^{-1} \pmod{p_i}$，
> 构造 $a = b_1 M_1 m_1 + b_2 M_2 m_2 + \cdots$，
> 则 $b = a \bmod (p_1 p_2 \cdots p_n)$。

**为什么对**：$M_i$ 是除 $p_i$ 外所有模数的乘积，所以

$$M_j m_j \equiv \begin{cases} 1 \pmod{p_i} & j = i \\ 0 \pmod{p_i} & j \ne i \end{cases}$$

于是 $a \equiv b_i \cdot 1 + \sum_{j\ne i} b_j \cdot 0 = b_i \pmod{p_i}$，每个方程都满足。

**唯一性**：若 $x, y$ 都满足，则 $p_i \mid (x-y)$ 对所有 $i$ 成立，
由互质得 $\prod p_i \mid (x-y)$，所以模 $\prod p_i$ 意义下唯一。

```python
# [片段]
def crt(rem, mod):
    """中国剩余定理（模数**两两互质**）。

    求 x 满足 x ≡ rem[i] (mod mod[i])，返回 (x, M)，M = ∏ mod[i]。
    复杂度 O(n log M)。Python 大整数天然不溢出，M 可以任意大。
    """
    M = 1
    for m in mod:
        M *= m                               # 所有模数的乘积，也是最终答案的模
    x = 0
    for r, m in zip(rem, mod):
        Mi = M // m                          # Mi 含除 m 外的全部因子，故 Mi ≡ 0 (mod 其他模数)
        x += r * Mi * pow(Mi, -1, m)         # pow(_, -1, m) 就是逆元
                                             # 这一项模 m 时等于 r，模其他模数时等于 0
    return x % M, M                          # 各项互不干扰地叠加，最后归约到 [0, M)
```

> **C++ 写这段要担心 $b_i M_i m_i$ 溢出 `long long`**（$M$ 到 $10^{18}$ 时乘法必爆），
> 得上龟速乘（`mulmod`）。**Python 完全没有这个问题**——
> 这是大整数带来的实打实的优势，见 [高精度与大整数](../../toolkit/bignum.md)。

**典型用途**：

| 场景 | 用法 |
| --- | --- |
| 模数太大 / 不是质数 | 拆成若干质数幂，分别算再 CRT 合并（Lucas 定理的扩展就是这么干的） |
| 高精度乘法加速 | 找多个互质的模数，求出高精度数在各个模数下的运算结果，再用中国剩余定理合并 |
| 循环节合并 | 两个周期分别是 $p, q$ 且同时满足某条件的最早时刻 |

---

## 4　扩展 CRT（模数**不互质**）

更一般的问题是：

> $a \bmod p_i = b_i$，已知 $p_i$ 和 $b_i$，求 $b = a \bmod \operatorname{lcm}(p_1 \cdots p_n)$ 的值。
> 求出 $\operatorname{lcm}(p_1 \dots p_n)$，然后借此构造一组互质的 $(q_1, \dots, q_t)$，
> 并求出 $a \bmod q_i$ 的值 $c_i$，然后用上题的做法继续做。

一条路线是「先质因数分解再拆开」。**实战里更常用「两两合并」的路线**，
不需要分解质因数，代码更短：

**把两个同余式合并成一个**。已有 $x \equiv r_0 \pmod{m_0}$，要再满足 $x \equiv r_1 \pmod{m_1}$。
写 $x = r_0 + m_0 t$，代入第二式：

$$m_0 t \equiv r_1 - r_0 \pmod{m_1}$$

设 $g = \gcd(m_0, m_1)$。这个方程**有解当且仅当 $g \mid (r_1 - r_0)$**，
此时两边同除 $g$：

$$\frac{m_0}{g}\, t \equiv \frac{r_1-r_0}{g} \pmod{\frac{m_1}{g}}$$

现在 $\gcd(m_0/g,\ m_1/g) = 1$，逆元存在：

$$t \equiv \frac{r_1-r_0}{g}\left(\frac{m_0}{g}\right)^{-1} \pmod{\frac{m_1}{g}}$$

代回得新的 $x \equiv r_0 + m_0 t \pmod{\operatorname{lcm}(m_0, m_1)}$。

```python
# [片段]
from math import gcd


def excrt(rem, mod):
    """扩展 CRT：模数**不必互质**。

    求 x 满足 x ≡ rem[i] (mod mod[i])，返回 (x, L)，L = lcm(mod[i])；
    **无解返回 None**。复杂度 O(n log L)。
    """
    r0, m0 = 0, 1                            # 当前解：x ≡ r0 (mod m0)
                                             # 初值 (0, 1) 表示「还没有任何约束」，任何整数都满足
    for r1, m1 in zip(rem, mod):             # 每轮把一个新方程合并进当前解
        g = gcd(m0, m1)
        diff = r1 - r0                       # 令 x = r0 + m0*t，代入后要解 m0*t ≡ diff (mod m1)
        if diff % g:                         # ★ 无解判定
            return None                      # 左边恒是 g 的倍数，diff 不是就永远配不上
        lcm = m0 // g * m1                   # 先除后乘，避免中间量过大（C++ 尤其重要）
        mm = m1 // g                          # 三边同除 g 后，新模数是 mm，且与 m0/g 互质
        t = (diff // g) % mm * pow(m0 // g, -1, mm) % mm   # 解出 t 的最小非负代表
        r0 = (r0 + m0 * t) % lcm             # 代回 x = r0 + m0*t，得到新解
        m0 = lcm                             # 新解的周期是两个模数的最小公倍数
    return r0, m0
```

**自测**：

| 输入 | 输出 | 说明 |
| --- | --- | --- |
| `excrt([2,3,2], [3,5,7])` | `(23, 105)` | 韩信点兵，经典解 23 |
| `excrt([3,5], [4,6])` | `(11, 12)` | 不互质但有解 |
| `excrt([1,2], [4,6])` | `None` | $\gcd(4,6)=2$，但 $2-1=1$ 不是 2 的倍数 → 无解 |
| `excrt([2,5], [4,6])` | `None` | 同上 |

> **三个坑**：
> 1. **`lcm = m0 // g * m1` 必须先除后乘**。虽然 Python 不会溢出，
>    但先乘会产生一个大一倍的中间量，在 $n$ 很大时白白浪费时间；
> 2. **`pow(x, -1, 1)` 在 Python 里返回 0**（模 1 意义下一切同余），
>    所以 `mm == 1` 时不需要特判，代码天然正确；
> 3. **无解判定不能省**。扩展 CRT 与普通 CRT 最大的区别就是「可能无解」，
>    很多题的答案就是判无解。

---

## 5　BSGS：大步小步求离散对数

**问题**：

> $a^x \equiv b \pmod p$，已知 $a, b, p$，求 $x$。$a, b \le p \le 10^{12}$，$p$ 为素数。

这叫**离散对数问题**（discrete logarithm）。$p$ 到 $10^{12}$，暴力枚举 $x$ 不可能。

**算法**：

> 设 $t = \sqrt{p}$，设 $x = ct - g$，则 $a^{ct-g} = b$，即 $a^{ct} = b \cdot a^{g}$。
> 先求出 $a^{0t}, a^{1t}, a^{2t}, \dots$ 并保存到 map 中，
> 然后求 $b\cdot a, b\cdot a^2, b\cdot a^3, \dots$ 并不断在 map 中测试对应值是否存在。
> 如果某次测试存在：$b\cdot a^{g} = a^{ct}$，那么就可以算出 $x = ct - g$。

**这就是「中途相遇」（meet in the middle）**：把一维的 $O(p)$ 枚举拆成两个 $O(\sqrt p)$ 的枚举，
用哈希表把两边对上。

| 步骤 | 名字 | 做什么 | 次数 |
| --- | --- | --- | --- |
| 先算 $b \cdot a^{j}$，$j = 0..m-1$ | **小步**（baby step） | 存进 `dict` | $m = \lceil\sqrt p\rceil$ |
| 再算 $(a^m)^i$，$i = 1..m$ | **大步**（giant step） | 在 `dict` 里查 | $m$ |

命中时 $a^{im} = b\,a^{j}$，即 $a^{im-j} = b$，所以 $x = im - j$。

因为任意 $x \in [0, p-1]$ 都能写成 $im - j$（$1\le i\le m$，$0\le j < m$），
所以**不会漏解**，而且**第一次命中给出的就是最小解**（$i$ 从小到大、$j$ 在 `dict` 里被后写的覆盖成更大的）。

**分块的直觉**：把 $[0, p)$ 这条长度 $p$ 的数轴切成 $m = \lceil\sqrt p\rceil$ 段，每段长 $m$。
指数 $x$ 落在第 $i$ 段里的第几个位置，就由 $(i, j)$ 这一对下标唯一确定。
枚举「哪一段」是 $m$ 次大步，枚举「段内第几个」是 $m$ 次小步，
一维的 $p$ 次枚举于是变成两轮各 $\sqrt p$ 次。

**哈希表里存的是什么**：键是 $b\,a^{j} \bmod p$ 这个**具体的数值**，
值是产生它的那个指数 $j$。大步阶段算出一个 $(a^m)^i \bmod p$，
就拿这个数值去表里问「有没有哪个小步算出过同一个数」。
问到了就说明 $a^{im} \equiv b\,a^{j}$，两边同除 $a^{j}$ 即 $a^{im-j} \equiv b$。
**所以表是「数值 → 指数」的反查表，本质上是在做一次以数值为媒介的对撞。**

```python
# [片段]
from math import isqrt


def bsgs(a, b, p):
    """求最小非负整数 x 使 a^x ≡ b (mod p)。要求 gcd(a, p) = 1。

    无解返回 -1。复杂度 O(sqrt(p))，空间 O(sqrt(p))。
    p = 1e12 时 m = 1e6，Python 约 2-4 秒 —— 已是上限。
    """
    a %= p
    b %= p
    if p == 1:
        return 0                             # 模 1 下人人同余，0 就是答案
    if b == 1:
        return 0                             # a^0 = 1，最小解是 0
    m = isqrt(p - 1) + 1                     # m = ceil(sqrt(p))
    tbl = {}                                 # 数值 -> 指数 j 的反查表
    cur = b
    for j in range(m):                       # 小步：b * a^j
        tbl[cur] = j                         # 同值时后写的 j 更大 -> 保证 x = i*m - j 最小
        cur = cur * a % p                    # 递推比每次 pow 快得多，每步只一次乘和一次取模
    am = pow(a, m, p)                        # 大步的步长：一步跨过 m 个指数
    cur = 1
    for i in range(1, m + 1):                # 大步：(a^m)^i
        cur = cur * am % p                   # 从 i=1 起，因为 i=0 对应 x<=0，已被 b==1 处理
        if cur in tbl:
            return i * m - tbl[cur]          # 命中：a^(im) = b*a^j，故 a^(im-j) = b
    return -1                                # i 枚举到 m 仍未命中，说明 b 不在 a 生成的循环里
```

**自测**：`bsgs(2,3,5) == 3`（$2^3=8\equiv3$）、`bsgs(3,4,7) == 4`、
`bsgs(2,6,11) == 9`、`bsgs(2,0,11) == -1`。

> **`tbl[cur] = j` 不加 `if cur not in tbl` 是有意为之**：
> 同一个值 `cur` 若出现多次，要保留**最大**的 $j$，
> 这样 $x = im - j$ 才最小。写成「只存第一个」会得到偏大的解。

### 扩展 BSGS（$\gcd(a,p) \ne 1$）

当 $a$ 与 $p$ 不互质时上面的算法失效（$a$ 没有逆元）。做法：不断提取公因子。

```python
# [片段]
def exbsgs(a, b, p):
    """扩展 BSGS：不要求 gcd(a, p) = 1。无解返回 -1。"""
    a %= p; b %= p
    if b == 1 or p == 1:
        return 0
    cnt = 0                                  # 已经提出去的公因子个数，也是已经确定的指数部分
    d = 1                                    # 提取过程中攒下的系数，满足 d*a^y ≡ b 的那个 d
    while True:
        g = gcd(a, p)
        if g == 1:
            break                            # 互质了，剩下的部分可以交给普通 BSGS
        if b % g:
            return -1                        # b 不含因子 g -> 无解
        b //= g; p //= g; d = d * (a // g) % p   # 方程三边同除 g，多出的 a/g 记进 d
        cnt += 1                             # 每除一次相当于确定了 x 的一位，指数加 1
        if b == d:
            return cnt                       # 提取过程中已经凑出答案
    # 现在 gcd(a, p) = 1，解 d * a^y ≡ b (mod p)
    r = bsgs(a, b * pow(d, -1, p) % p, p)    # 把 d 挪到右边变成标准形式 a^y ≡ b/d
    return -1 if r < 0 else r + cnt          # 真正的指数是提取阶段的 cnt 加上后半段的 y
```

> **竞赛里 exBSGS 出现频率远低于 BSGS**。看到「$p$ 是质数」就直接用普通版。

### Python 的可行规模

| $p$ | $m = \sqrt p$ | 小步 + 大步的 Python 层迭代 | 估时 |
| --- | --- | --- | --- |
| $10^9$ | $3.2\times10^4$ | $6.4\times10^4$ | 0.05 s ✅ |
| $10^{12}$ | $10^6$ | $2\times10^6$ | **2–4 s** ⚠️（`dict` 有 $10^6$ 个键，约 80MB） |
| $10^{14}$ | $10^7$ | $2\times10^7$ | ❌ 内存先炸 |

> **BSGS 的瓶颈在 Python 里是 `dict` 而不是循环**：
> $10^6$ 个键的 `dict` 占约 80MB，插入 $10^6$ 次约 0.5 秒。
> 如果卡内存，可以把小步的结果存成排好序的 `list` 再 `bisect`（省一半内存，慢一点）。

---

## 6　高斯消元

问题描述：

> 已知 $a_{i,j}$、$b_i$（$i,j = 1..n$），且 $\sum_j a_{i,j} x_j = b_i$，
> 求一组可行的 $x_i$ 使上式成立。数据保证一定存在解。

还有一句提醒：

> 拉格朗日插值法不会也没关系，但是**高斯消元建议学习一番**。

**算法三步**：

1. **选主元**：在第 $i$ 列里找绝对值最大的行（浮点版）或非零的行（模意义版），换到第 $i$ 行；
2. **消元**：把第 $i$ 行的倍数减到下面所有行，使第 $i$ 列以下全为 0；
3. **回代**：从最后一行往上依次求出 $x_n, x_{n-1}, \dots, x_1$。

复杂度 $O(n^3)$。

### 浮点版

```python
# [片段]
def gauss(a, n):
    """解 n 元线性方程组。a 是 n 行 (n+1) 列的增广矩阵（浮点），**会被原地修改**。

    返回解向量；若无唯一解返回 None。复杂度 O(n^3)。
    Python 下 n <= 200 约 1 秒；n <= 300 约 3 秒。
    """
    EPS = 1e-9
    for i in range(n):
        # 1) 选主元：绝对值最大的行 —— 这是**数值稳定性的关键**，不能省
        piv = i
        best = abs(a[i][i])
        for r in range(i + 1, n):
            v = abs(a[r][i])
            if v > best:
                best = v; piv = r
        if best < EPS:
            return None                      # 该列全 0 -> 无解或无穷多解
        if piv != i:
            a[i], a[piv] = a[piv], a[i]      # 整行交换，Python 里是两个引用互换，几乎不花钱
        # 2) 消元
        row = a[i]
        inv = 1.0 / row[i]                   # 主元的倒数只算一次，内层用乘法代替除法
        for r in range(i + 1, n):
            f = a[r][i] * inv                # f 是让第 r 行第 i 列归零所需的倍数
            if f:                            # 已经是 0 就跳过整行，稀疏矩阵上省很多
                ar = a[r]
                for c in range(i, n + 1):    # 内层循环是 O(n^3) 的来源
                    ar[c] -= row[c] * f      # 从第 i 列开始就够：左边各列本轮之前已归零
    # 3) 回代
    x = [0.0] * n
    for i in range(n - 1, -1, -1):           # 从最后一行往上，此时右边的未知数都已求出
        s = a[i][n]                          # 第 n 列是增广矩阵的常数项
        row = a[i]
        for j in range(i + 1, n):
            s -= row[j] * x[j]               # 把已知的 x[j] 移到等号右边
        x[i] = s / row[i]                    # 剩下只有 x[i] 一个未知数
    return x
```

> **「选绝对值最大的行当主元」（列主元消去法）不是可选优化，是必需品**。
> 用一个接近 0 的主元去除，误差会被放大几个数量级，
> $n = 100$ 时结果可能面目全非。这是浮点高斯消元的第一大坑。

### 模意义版（**更适合竞赛**）

模素数 $p$ 意义下，除法换成乘逆元，**没有任何精度问题**：

```python
# [片段]
def gauss_mod(a, n, p):
    """模 p（**素数**）意义下解线性方程组。a 是 n×(n+1) 的整数增广矩阵，原地修改。

    返回解向量；主元不足时返回 None（无解或多解）。复杂度 O(n^3)。
    """
    for i in range(n):
        piv = -1
        for r in range(i, n):
            if a[r][i] % p:                  # 模意义下只要非零即可，不存在「数值稳定性」
                piv = r
                break
        if piv < 0:
            return None                      # 整列都是 0，方程不独立：无解或多解
        if piv != i:
            a[i], a[piv] = a[piv], a[i]
        row = a[i]
        inv = pow(row[i], -1, p)             # p 是素数，非零元一定有逆元
        for c in range(i, n + 1):            # 把主元行整体归一化
            row[c] = row[c] * inv % p        # 主元变成 1，后面消元就不用再做除法
        for r in range(n):
            if r != i and a[r][i]:           # 对**所有**行消元（含上方），做成约当消元
                f = a[r][i]                  # 主元已归一，倍数直接就是该行第 i 列的值
                ar = a[r]
                for c in range(i, n + 1):
                    ar[c] = (ar[c] - row[c] * f) % p
    return [a[i][n] % p for i in range(n)]   # 矩阵已化为单位阵，常数列即答案，无需回代
```

### 异或方程组（**Python 的绝活**）

高斯消元还能解异或方程组。
这是模 2 意义下的高斯消元，Python 可以用**大整数当位向量**，把一整行压成一个 `int`：

```python
# [片段]
def gauss_xor(rows, nvar):
    """异或方程组：rows[i] 是一个整数，低 nvar 位是系数，第 nvar 位是常数项。

    返回一组解（整数的低 nvar 位）；无解返回 None。
    ★ 每次消元是一次大整数异或 —— 整行操作在 C 层完成，比逐位快几十倍。
    """
    n = len(rows)
    where = [-1] * nvar                      # where[c] = 以第 c 个变量为主元的那一行；-1 = 自由变量
    r = 0                                    # 已确定主元的行数，也是下一个主元行的位置
    for c in range(nvar):
        piv = -1
        for i in range(r, n):
            if (rows[i] >> c) & 1:           # 取第 c 位：这一行的第 c 个系数是不是 1
                piv = i
                break
        if piv < 0:
            continue                         # 该列全 0 -> 第 c 个变量自由，取 0 即可
        rows[r], rows[piv] = rows[piv], rows[r]
        where[c] = r
        pr = rows[r]
        for i in range(n):
            if i != r and ((rows[i] >> c) & 1):
                rows[i] ^= pr                # ★ 一次异或消掉一整行
        r += 1                               # 主元行用掉一行，下一个主元只能在更下面找
    for i in range(r, n):                    # 剩下的都是系数全 0 的行
        if rows[i] == (1 << nvar):           # 0 = 1 -> 无解
            return None
    x = 0
    for c in range(nvar):
        if where[c] >= 0 and (rows[where[c]] >> nvar) & 1:   # 取该行的常数项位
            x |= 1 << c                      # 常数项为 1 则该变量取 1，自由变量一律取 0
    return x
```

> **这是 Python 相对 C++ 的一个真实优势**：C++ 要写 `bitset<N>`，
> Python 直接用内置大整数，`rows[i] ^= pr` 一行搞定，
> 而且位数没有编译期上限。$n = 2000$ 的异或方程组在 Python 里也能秒过。

### 可行规模

| 版本 | 复杂度 | Python 可行的 $n$ |
| --- | --- | --- |
| 浮点高斯消元 | $O(n^3)$ | $n \le 200$ ✅，$n \le 300$ ⚠️ |
| 模意义高斯消元 | $O(n^3)$，每步还有一次取模 | $n \le 150$ ⚠️ |
| **异或高斯消元（大整数位向量）** | $O(n^2)$ 次大整数异或 | **$n \le 2000$ ✅** |
| 用 `numpy` 做浮点消元 | $O(n^3)$ 全在 C 层 | $n \le 1000$ ✅（**但牛客可能没装 numpy，别赌**） |

---

## 7　例题

<!-- CHAPTER-EXAMPLE-TABLE -->

### BISHI74 【模板】非质模数下的乘法逆元（中等）

> $T \le 10^4$ 组，每组给 $a, m$（$1\le a < m \le 10^9$），求 $a^{-1} \bmod m$。
> **数据不保证 $m$ 为质数。**
> 题面见 [原题](https://www.nowcoder.com/practice/52328883c41f475c8eb228726af2ce2f)。

> ✅ 题解见 [`solutions/nowcoder/BISHI74/sol.py`](../../solutions/BISHI74.md)，**已通过官方样例验证**。

**「非质模数」四个字直接判了费马小定理死刑**：$a^{m-2}$ 只有在 $m$ 是质数时才是逆元。
必须用扩展欧几里得。

```python
import sys


def inv(a: int, m: int) -> int:
    """扩展欧几里得求 a 在模 m 下的逆元；不存在返回 -1。迭代版，无递归开销。"""
    # 维护 old_r = old_s * a + (...) * m，对 (r, s) 做辗转相除
    old_r, r = a, m                          # 余数列：辗转相除到 r 为 0 时 old_r 就是 gcd
    old_s, s = 1, 0                          # a 的系数列；m 的系数用不到，不维护
    while r:
        q = old_r // r
        old_r, r = r, old_r - q * r
        old_s, s = s, old_s - q * s          # 系数跟着余数做同样的线性组合
    if old_r != 1:                           # gcd(a, m) != 1 -> 逆元不存在
        return -1
    return old_s % m                         # 可能是负数，拉回 [0, m)


def main() -> None:
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    out = []
    for i in range(t):
        # 第 i 组的两个数紧挨着，跳过开头的 t 后按 2 步长定位
        a = int(data[1 + 2 * i]); m = int(data[2 + 2 * i])
        # 等价一行写法（Python 3.8+）：
        #   try: v = pow(a, -1, m)
        #   except ValueError: v = -1
        out.append(str(inv(a, m)))
    sys.stdout.write("\n".join(out) + "\n")


main()
```

**四个要点**：

1. **只留 $s$ 不留 $t$**：只要 $x$（即 $a$ 的系数），$y$ 用不上，
   少维护一组变量能省三分之一的时间；
2. **`old_s % m` 必须做**：exgcd 出来的 $x$ 可能是负数。
   Python 的 `%` 对负数返回非负结果，比 C++ 的 `((x%m)+m)%m` 省心；
3. **迭代不递归**：$T = 10^4$ 时递归的函数调用开销明显，且完全没必要；
4. 逆元不存在时题面没规定输出什么（题面歧义），本解按竞赛惯例输出 $-1$，
   不影响有解数据的正确性。

> **这题就是 CRT 的零件**：`excrt` 里的
> `pow(m0 // g, -1, mm)` 处理的正是「模数 `mm` 可能不是质数」的情形，
> 和本题一模一样。**把这题写熟，CRT 就只剩一个循环。**

### BISHI65 【模板】分数取模（中等）

> $t \le 10^4$ 组，每组给 $a, b$（$-10^9 \le a \le 10^9$，$1 \le b \le 10^9$），
> 求 $\dfrac{a}{b} \bmod P$，$P = 10^9+7$ 为质数。
> 题面见 [原题](https://www.nowcoder.com/practice/23839ef20d5f4dbaa9664daa51864291)。

> ✅ 题解见 [`solutions/nowcoder/BISHI65/sol.py`](../../solutions/BISHI65.md)，**已通过官方样例验证**。

**和 BISHI74 恰好互补**：这题的模数**是质数**，所以费马小定理可用。

$$b^{P-1}\equiv 1 \pmod P \;\Longrightarrow\; b^{-1} \equiv b^{P-2} \pmod P$$

```python
import sys

P = 1000000007                               # 题面给定的质数模数，费马小定理适用


def main() -> None:
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    out = []
    ap = out.append                          # 绑成局部名字，1e4 次循环里省掉属性查找
    for i in range(t):
        # 第 i 组的 a、b 紧挨着，跳过开头的 t 后按 2 步长定位
        a = int(data[1 + 2 * i]); b = int(data[2 + 2 * i])
        # 等价写法：inv = pow(b, -1, P)（走扩展欧几里得，不要求 P 是质数）
        ap(str(a * pow(b, P - 2, P) % P))    # Python 的 % 天然把负数拉回 [0, P)
    sys.stdout.write("\n".join(out) + "\n")


main()
```

**三个坑**：

1. **$a$ 可能是负数**。Python 的 `%` 永远返回非负结果，所以 `a * inv % P` 天然落在 $[0, P-1]$；
   C++ 必须写 `((x % P) + P) % P`；
2. $1 \le b \le 10^9 < P$，所以 $b \not\equiv 0$，逆元一定存在，不用判退化；
3. **别真的去算浮点 `a / b` 再取模**，那是完全不同的东西。

> **两题合起来给出了完整的判断树**：
>
> ```text
> 要算模意义下的除法 / 逆元
>   ├─ 模数是质数        -> pow(b, P-2, P)   （费马小定理）
>   ├─ 模数不是质数      -> pow(b, -1, m)    （扩展欧几里得，需 gcd(b,m)=1）
>   ├─ 要算 1..n 全部逆元 -> 线性递推 O(n)
>   └─ gcd(b, m) != 1    -> 逆元不存在，改用扩展 CRT / 提取公因子
> ```

### 两道例题与本章主题的距离

诚实地说：BISHI74 和 BISHI65 只覆盖了本章的**第一节**（逆元）。
CRT、BSGS、高斯消元在配套题单里**没有对应题目**。

| 想练手 | 推荐题 |
| --- | --- |
| CRT | P1495【模板】中国剩余定理 |
| 扩展 CRT | P4777【模板】扩展中国剩余定理 |
| BSGS | P3846 / SDOI2011 计算器 |
| 高斯消元 | P3389【模板】高斯消元法 |
| 异或高斯消元 | P2447 外星千足虫 |

---

## 8　本章速查

| 要点 | 结论 |
| --- | --- |
| 逆元存在条件 | **$\gcd(a,m)=1$** |
| 质模数求逆 | `pow(a, p - 2, p)`（费马小定理） |
| **任意模数求逆** | **`pow(a, -1, m)`**（Python 3.8+，内部是 exgcd） |
| exgcd 的解 | 可能是**负数**，要 `% m` 拉回 |
| Python 的 `%` | 对负数返回**非负**结果，比 C++ 省一步 |
| **CRT 构造** | $x = \sum b_i M_i m_i$，$M_i = M/p_i$，$m_i = M_i^{-1} \bmod p_i$ |
| CRT 的前提 | 模数**两两互质** |
| **扩展 CRT** | **两两合并**：$m_0 t \equiv r_1-r_0 \pmod{m_1}$ |
| exCRT 无解判定 | **$g \nmid (r_1-r_0)$** |
| exCRT 的 lcm | **先除后乘** `m0 // g * m1` |
| Python 的 CRT 优势 | 大整数不溢出，**不需要龟速乘** |
| **BSGS** | $x = im - j$，小步存 $b\,a^j$，大步查 $(a^m)^i$ |
| BSGS 复杂度 | $O(\sqrt p)$ 时间与空间 |
| BSGS 求最小解 | `tbl[cur] = j` **不加 `if not in`**（要保留最大的 $j$） |
| BSGS 的前提 | $\gcd(a,p)=1$；否则用 exBSGS 提取公因子 |
| 高斯消元 | 选主元 → 消元 → 回代，$O(n^3)$ |
| **浮点消元** | **必须选绝对值最大的主元**，否则误差爆炸 |
| 模意义消元 | 除法换成 `pow(x, -1, p)`，**零精度问题** |
| **异或方程组** | **一行压成一个大整数**，消元 = 一次 `^`，Python 的绝活 |

| 数据规模 → Python 现实性（本章算法） |
| --- |
| exgcd / 逆元，$T \le 10^5$ | ✅ 稳 |
| CRT / exCRT，$n \le 10^5$ 个方程 | ✅ 稳 |
| BSGS，$p \le 10^9$ | ✅ 0.05 秒 |
| BSGS，$p \le 10^{12}$ | ⚠️ 2–4 秒 + 80MB 内存 |
| BSGS，$p \ge 10^{14}$ | ❌ 内存先炸 |
| 浮点高斯消元，$n \le 200$ | ✅ |
| 浮点高斯消元，$n \ge 400$ | ❌ $6\times10^7$ 次内层循环 |
| 模意义高斯消元，$n \le 150$ | ⚠️ |
| **异或高斯消元，$n \le 2000$** | ✅ **大整数位向量** |

---
id: toolkit/float
title: 浮点与科学计数法
volume: 1
lang: py
---

# 第 23 章　浮点与科学计数法

<!-- CHAPTER-EXAMPLES -->

浮点是算法题里最不起眼、却最容易无声无息 WA 的地方。
本章讲三件事：**误差从哪来、怎么避开、以及什么时候必须换掉 `float`**。

---

## 1　误差从哪来

`float` 是 IEEE 754 双精度：1 位符号 + 11 位指数 + 52 位尾数，
能精确表示的只有形如 $m \cdot 2^e$ 的数。**0.1 在二进制里是无限循环小数**，
就像 $1/3$ 在十进制里是 0.333… 一样：

```python
>>> 0.1 + 0.2
0.30000000000000004
>>> 0.1 + 0.2 == 0.3
False
>>> from decimal import Decimal
>>> Decimal(0.1)
Decimal('0.1000000000000000055511151231257827021181583404541015625')
```

最后一行揭示了本质：`0.1` 这个字面量存进去的**根本不是 0.1**。

有效数字约 15–17 位。超过这个精度的整数，转成 `float` 就开始丢：

```python
>>> float(10 ** 17) == 10 ** 17
True
>>> float(10 ** 17 + 1) == 10 ** 17 + 1
False               # 已经分不清了
>>> int(10 ** 18 ** 0.5)
```

**推论：算法题里凡是能用整数表达的，就绝不要经过 `float`。**

| 想做的事 | ❌ 浮点写法 | ✅ 整数写法 |
| --- | --- | --- |
| 判断 $a/b = c/d$ | `a/b == c/d` | `a * d == b * c` |
| 判断 $a/b > c/d$（$b,d>0$） | `a/b > c/d` | `a * d > b * c` |
| 整除判断 | `a / b == a // b` | `a % b == 0` |
| 开方判完全平方 | `int(x**0.5)**2 == x` | `math.isqrt(x)**2 == x` |
| 取中点 | `(l + r) / 2` | `(l + r) // 2` |
| 平均数比较 | 算平均值 | 比较总和（同分母时） |

`math.isqrt` 这条尤其重要：

```python
>>> x = 10 ** 18
>>> int(x ** 0.5)        # 999999999    错了！
>>> math.isqrt(x)        # 1000000000   对
```

判素数、找因子时用 `int(n ** 0.5)` 作循环上界，会因为这 1 的误差漏掉最后一个因子。
**永远用 `math.isqrt(n)`**（Python 3.8+）。

---

## 2　浮点比较

```python
EPS = 1e-9                             # 判等的容差，按题目要求的精度往下压两三个数量级

abs(x - y) < EPS                       # 相等：差值落在容差内就算同一个数
x > y + EPS                            # 严格大于：要超出容差才算真的大
x < y - EPS                            # 严格小于
abs(x - y) < EPS * max(1.0, abs(x))    # 相对误差版：x 很大时绝对误差本来就会变大
```

EPS 该取多少，取决于题目要求的精度和运算规模：

| 题目要求 | 建议 EPS |
| --- | --- |
| 误差 $10^{-6}$ | `1e-9` |
| 误差 $10^{-9}$ | `1e-12` |
| 实数二分，坐标范围 $10^9$ | 用**固定迭代次数**代替 EPS（见下） |

**实数二分不要用 `while r - l > EPS`**——量级大时可能永远不收敛。
改用固定次数，100 次足够把区间缩小到 $2^{-100}$ 倍：

```python
lo, hi = 0.0, 1e18                     # 答案一定落在这个闭区间里
for _ in range(100):                   # 固定次数：每轮区间减半，100 轮后长度是原来的 2^-100
    mid = (lo + hi) / 2
    if check(mid):                     # mid 已经满足条件 ⇒ 答案不会更大，收右端
        hi = mid
    else:                              # mid 不满足 ⇒ 答案只可能在右半边，抬左端
        lo = mid
print("%.6f" % lo)                     # 区间已经窄到远小于输出精度，取哪一端都行
```

详见 [二分](../basic/binary-search.md)。

---

## 3　舍入：Python 用的是「四舍六入五成双」

这是 PIO14 里详细讲过的坑，这里补充完整规则。

`round()`、`"%.nf"`、`f"{x:.nf}"`、`format()` **全部**使用
**banker's rounding（向偶数舍入）**：遇到恰好 .5 时，舍入到最近的偶数。

```python
>>> round(0.5), round(1.5), round(2.5), round(3.5)
(0, 2, 2, 4)
>>> "%.0f" % 2.5
'2'
>>> "%.2f" % 0.125
'0.12'
```

为什么这么设计？因为大批量数据下，「逢五进一」会系统性地偏大，
向偶数舍入在统计上无偏。但**算法题要的是数学上的四舍五入**。

正确做法是换掉整套小数运算，用 `decimal` 模块：

```python
from decimal import Decimal, ROUND_HALF_UP

# quantize 的第一个参数只看它有几位小数：Decimal("0.000") 就是保留 3 位并自动补零
Decimal("1.2345").quantize(Decimal("0.000"), rounding=ROUND_HALF_UP)   # 1.235
Decimal("2.5").quantize(Decimal("1"), rounding=ROUND_HALF_UP)          # 3，不是默认的 2
```

这行代码里有三个名字，各管一件事：

**`Decimal`** 是**十进制**小数类型。`float` 用二进制存数，`0.1` 存不进去（§1）；
`Decimal` 直接存十进制数字序列和一个指数，`Decimal("0.1")` 就是不多不少的 0.1。
代价是它比 `float` 慢，但没有想象中那么夸张——具体倍数见 §4。

**`quantize`** 是「**把小数位数量化到指定精度**」，也就是严格意义上的「保留 n 位小数」。
名字里的 quantize 是「对齐到刻度」的意思——参数给的那个 `Decimal` 就是刻度：

```python
Decimal("1.2345").quantize(Decimal("0.01"))   # 1.23   刻度 0.01 → 保留 2 位
Decimal("1.2345").quantize(Decimal("0.001"))  # 1.234  刻度 0.001 → 保留 3 位
Decimal("1.2").quantize(Decimal("0.000"))     # 1.200  位数不够会补零
Decimal("1.6").quantize(Decimal("1"))         # 2      刻度 1 → 舍入到整数
```

**参数只看有几位小数，不看具体数值**，所以 `Decimal("0.01")` 和 `Decimal("9.99")`
效果完全一样，惯例是写 `Decimal("0.01")` 这种一眼能数清位数的形式。
它和 `round()` 的区别在于：`quantize` 的结果**位数是固定的**，
`Decimal("1.2").quantize(Decimal("0.000"))` 会补成 `1.200`，
而 `round(1.2, 3)` 还是 `1.2`——输出「保留 3 位小数」时这一条直接决定对错。

**`ROUND_HALF_UP`** 是舍入模式，即「**遇到恰好一半时往上走**」，
也就是数学课上的四舍五入。名字拆开看：`HALF` 指「正好卡在中间的那一档」，
`UP` 指「往绝对值大的方向走」。对照着 Python 默认的 `ROUND_HALF_EVEN`
（一半时靠向偶数）：

```python
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN

q = Decimal("1")
[Decimal(x).quantize(q, rounding=ROUND_HALF_UP)   for x in ("0.5", "1.5", "2.5", "3.5")]
# [1, 2, 3, 4]                               ← 全部进位，符合数学直觉
[Decimal(x).quantize(q, rounding=ROUND_HALF_EVEN) for x in ("0.5", "1.5", "2.5", "3.5")]
# [0, 2, 2, 4]                                 ← 靠向偶数，round() 就是这个
```

**不写 `rounding=` 就是 `ROUND_HALF_EVEN`**（准确说是取当前上下文的默认值，
默认值就是它）。所以「用了 `Decimal` 还是答案不对」的第一嫌疑，是漏了这个参数。

**两个关键细节**：

1. **必须从字符串构造 `Decimal`**。`Decimal(1.005)` 会先经过 `float`，
   拿到的是 `1.00499999...`，白搭：

   ```python
   Decimal("1.005")     # Decimal('1.005')            ✅ 精确
   Decimal(1.005)       # Decimal('1.00499999...')    ❌ 已经错了
   ```

2. `quantize` 的参数决定小数位数：`Decimal("0.000")` 是 3 位，`Decimal("1")` 是整数。

`decimal` 的其它舍入模式：

| 模式 | 含义 |
| --- | --- |
| `ROUND_HALF_UP` | 数学四舍五入 ← 竞赛用这个 |
| `ROUND_HALF_EVEN` | 银行家舍入（Python 默认） |
| `ROUND_DOWN` | 向零截断 |
| `ROUND_FLOOR` | 向下取整 |
| `ROUND_CEILING` | 向上取整 |

---

## 4　什么时候该换掉 float

| 需求 | 用什么 |
| --- | --- |
| 高精度小数、金额、严格舍入 | `decimal.Decimal` |
| 精确分数（如概率、期望） | `fractions.Fraction` |
| 只需要判大小、不需要值 | 交叉相乘，全程整数 |
| 超大整数 | 原生 `int` |

### decimal

```python
from decimal import Decimal, getcontext

getcontext().prec = 50            # 有效数字位数（默认 28），管的是整体位数不是小数位数
a = Decimal("1") / Decimal("3")   # 除不尽时按 prec 截断，不会像 float 那样悄悄丢精度
print(a)                          # 0.33333333333333333333333333333333333333333333333333
```

`Decimal` 支持 `+ - * / **`、比较、`sqrt()`，也原生支持科学计数法输入。

**代价是慢，但要慢得有分寸。** CPython 3.3 起 `decimal` 由 C 扩展 `_decimal`
（底层是 libmpdec）实现，不再是纯 Python 版本。
3.9 环境下各跑 20 万次、取相对 `float` 的倍数：

| 运算 | `Decimal` 相对 `float` |
| --- | --- |
| `a * b` / `a + b` | 约 2–3 倍 |
| `a / b` | 约 3 倍 |
| 从字符串构造 | 约 1.5–2 倍 |
| 保留 2 位小数（`quantize` 对 `round`） | **约 0.9 倍，反而略快** |

也就是**基本算术慢 2–4 倍**，而不是一个数量级；`quantize` 甚至比 `round` 还略快。
（只记倍数不记毫秒，是因为绝对耗时随机器变，倍数关系稳定。）
真正会把 `Decimal` 拖垮的是把 `getcontext().prec` 调到几百位——精度越高越慢，
以及在 $10^6$ 级别的内层循环里逐个构造 `Decimal` 对象。
**结论不是「能不用就不用」，而是「别拿它当默认数值类型」**：
输入解析、最终舍入这类一次性的地方放心用，主循环里的算术还是走 `int`。

### fractions

```python
from fractions import Fraction

p = Fraction(1, 3) + Fraction(1, 6)     # 通分、相加、约分一步到位：Fraction(1, 2)
print(p.numerator, p.denominator)       # 分子分母分开取，输出既约分数时直接用：1 2
Fraction("0.25")                        # 从字符串构造是精确的：Fraction(1, 4)
```

期望/概率题里，如果答案要求以既约分数形式输出，`Fraction` 会自动约分。
但**分母会指数级膨胀**，$n$ 次运算后分母可能有上万位，慎用于大规模递推。

---

## 5　科学计数法

Python 原生支持科学计数法**字面量与解析**：

```python
>>> 1.5e3
1500.0
>>> float("1.23e-5")
1.23e-05
>>> Decimal("1.23E+5")          # Decimal 也支持，且精确
Decimal('1.23E+5')
```

### 输出成科学计数法

```python
>>> "%.3e" % 123456
'1.235e+05'
>>> f"{123456:.3e}"
'1.235e+05'
>>> f"{123456:.3g}"             # g 会自动在定点/科学之间选择
'1.23e+05'
```

`e` 格式的指数部分至少两位（`e+05`）。
**如果题目要的是 `1.235*10^5` 这种自定义格式，就得自己拼**——见下面的例题。

### 解析成 (尾数, 指数)

```python
s = "1.234e5"
# partition 按第一个 "e" 切成三段；转小写是为了同时容纳 "E" 写法
mant, _, exp = s.lower().partition("e")
mant = Decimal(mant)                    # 尾数走 Decimal，避开 float 的二进制误差
exp = int(exp) if exp else 0            # 没有 e 的部分时 exp 是空串，指数按 0 处理
```

或者用 `Decimal.as_tuple()` 直接拿到符号、数字序列、指数：

```python
>>> Decimal("1.234e5").as_tuple()
DecimalTuple(sign=0, digits=(1, 2, 3, 4), exponent=2)
```

---

## 6　例题

<!-- CHAPTER-EXAMPLE-TABLE -->

### PIO14 单组_保留小数位数

见 [输入输出处理 §6](io.md#保留小数位数)。核心是
`Decimal(字符串)` + `ROUND_HALF_UP`。题解：[`solutions/nowcoder/PIO14/sol.py`](../solutions/PIO14.md)

### PIO17 单组_spj判断浮点误差

> 求圆面积，误差 $10^{-3}$ 以内即可。

```python
import math

r = int(input())
# math.pi 带满双精度有效数字；输出 6 位小数远严于题目要求的 1e-3 误差
print("%.6f" % (math.pi * r * r))
```

两条准则：**用 `math.pi` 不要手写 3.14159**（$r=1000$ 时少两位小数就差 10 的量级，
远超 $10^{-3}$）；**输出位数宁多勿少**。题解：[`solutions/nowcoder/PIO17/sol.py`](../solutions/PIO17.md)

### BISHI14 特殊的科学计数法（简单）

> 给定一个大整数 $N$，输出其「特殊科学计数法」表示，形如 `a.b*10^c`。

这题是本章所有知识点的集合：**大整数不能转 float**（会丢精度）、
**舍入必须是数学四舍五入**、**进位溢出要特判**。

思路：设 $N$ 有 $L$ 位，则指数 $c = L - 1$。尾数取前几位数字，
按题目要求的位数做 `ROUND_HALF_UP` 舍入。

关键坑是**进位溢出**：如果尾数是 `9.9x` 且要舍入到 1 位小数，
结果会变成 `10.0`——这时必须改写成 `1.0*10^(c+1)`，而不是输出 `10.0*10^c`。

```python
from decimal import Decimal, ROUND_HALF_UP

s = input().strip()                             # 全程按字符串处理，不碰 int 也不碰 float
c = len(s) - 1                                  # L 位数写成 a.b 形式时，指数就是 L-1
# 只需要前几位，绝不把整个大整数转成 float
mant = Decimal(s[0] + "." + s[1:4])             # 首位当整数部分，后几位当小数部分
r = mant.quantize(Decimal("0.0"), rounding=ROUND_HALF_UP)   # 保留 1 位小数，数学四舍五入
if r >= 10:                                     # 进位溢出，如 9.95 -> 10.0
    r /= 10                                     # 尾数退回 [1, 10)
    c += 1                                      # 退掉的那一位加到指数上
print("{}*10^{}".format(r, c))
```

#### 另一种写法：根本不碰小数

上面那份代码用 `Decimal` 是为了把「四舍五入」这件事交给标准库，写法通用——
换成保留 3 位小数只要改一个 `Decimal("0.001")`。
但**这题保留的是固定 1 位小数**，进位规则可以直接手写，于是全程只有整数：

```python
import sys

N = sys.stdin.readline().strip()
a, b, c = int(N[0]), int(N[1]), len(N) - 1   # 首位、次位、指数 = 位数 - 1
if int(N[2]) >= 5:                           # 第 3 位决定次位是否进位（HALF_UP 的定义）
    b += 1
if b == 10:                                  # 次位进位溢出，向首位借
    b = 0
    a += 1
if a == 10:                                  # 首位也溢出：9.95 这类，规格化成 1.0
    a, b = 1, 0
    c += 1
print(f"{a}.{b}*10^{c}")
```

两份代码等价，`Decimal` 那份的 `quantize` 在这里退化成了「看第 3 位、必要时向前借位」
这三个 `if`。**能这么改写，是因为「保留 1 位」意味着整个小数部分只有一个数字**，
它的进位可以用整数加法表达；保留位数一多，手写进位链就不如 `quantize` 稳当。

选哪个的判据：**位数固定且很少**（1–2 位）时手写整数更短、更快、也不依赖 `decimal`；
**位数由输入决定**，或者还要参与其它小数运算，就用 `Decimal`。

> 完整实现见 [`solutions/nowcoder/BISHI14/sol.py`](../solutions/BISHI14.md)，
> 已通过官方样例验证。该题面对尾数保留位数的描述存在歧义，
> 题解文件的 docstring 里记录了歧义的两种读法及取舍依据。

---

## 7　本章速查

| 场景 | 结论 |
| --- | --- |
| 浮点相等 | `abs(x-y) < EPS`，绝不用 `==` |
| 分数比大小 | 交叉相乘，全程整数 |
| 整数开方 | `math.isqrt(n)`，绝不用 `n ** 0.5` |
| 实数二分 | 固定 100 次迭代，不要用 `while r-l > EPS` |
| 严格四舍五入 | `Decimal(字符串).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)` |
| `quantize` 的参数 | 只看它有几位小数，就是保留几位，且会补零 |
| 漏写 `rounding=` | 退回银行家舍入，等于白用 `Decimal` |
| `round()` / `%.nf` | 是银行家舍入，`round(2.5) == 2` |
| `Decimal` 构造 | **必须传字符串**，传 float 白搭 |
| 精确分数 | `fractions.Fraction`，但分母会膨胀 |
| 科学计数法解析 | `float(s)` 或 `Decimal(s)`，后者精确 |
| 科学计数法输出 | `"%.3e"`；自定义格式要自己拼 |
| spj 浮点题 | 输出位数宁多勿少 |

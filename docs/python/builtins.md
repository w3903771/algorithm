---
id: python/builtins
title: 内置函数速查
volume: 1
lang: py
---

# 第 13 章　内置函数速查

<!-- CHAPTER-EXAMPLES -->

内置函数（builtins）是**不需要 `import` 就能用**的一批函数，共 69 个。
它们全部由 C 实现，**是 Python 里唯一「免费」的循环**——
把一个 Python `for` 换成一个内置函数调用，通常能快 3–10 倍。

这一章先给全表分类，再对竞赛高频的 16 个逐一详解并标注复杂度。

---

## 1　全部内置函数按用途分类

### 类型构造与转换（14 个）

| 函数 | 作用 |
| --- | --- |
| `int(x[, base])` | 转整数；`base` 支持 2–36，`int("ff", 16)` → 255 |
| `float(x)` | 转浮点，支持 `"1e9"`、`"inf"`、`"nan"` |
| `bool(x)` | 转布尔，按假值表 |
| `complex(re, im)` | 转复数 |
| `str(x)` | 转字符串（可读形式） |
| `bytes(x)` / `bytearray(x)` | 字节串 / 可变字节串 |
| `list(x)` / `tuple(x)` | 转列表 / 元组 |
| `set(x)` / `frozenset(x)` | 转集合 / 不可变集合 |
| `dict(...)` | 建字典 |
| `memoryview(b)` | 零拷贝的字节视图（竞赛几乎用不到） |
| `object()` | 创建最基础的对象（用作唯一哨兵值） |

### 数学（8 个）

| 函数 | 作用 |
| --- | --- |
| `abs(x)` | 绝对值；复数则是模长 |
| `divmod(a, b)` | 一次返回 `(a // b, a % b)` |
| `pow(a, b[, m])` | 幂；三参数版是**快速幂取模** |
| `round(x[, n])` | 四舍六入五成双（**不是数学四舍五入**） |
| `sum(it[, start])` | 求和 |
| `max(...)` / `min(...)` | 最大 / 最小，支持 `key` 和 `default` |
| `hash(x)` | 哈希值（只对不可变对象） |

### 序列与迭代（12 个）

| 函数 | 作用 |
| --- | --- |
| `len(s)` | 长度，$O(1)$ |
| `range(...)` | 等差整数序列对象 |
| `enumerate(it[, start])` | 产生 `(下标, 元素)` |
| `zip(*its)` | 并行打包多个序列 |
| `reversed(seq)` | 反向迭代器 |
| `sorted(it, key, reverse)` | 排序，返回新列表 |
| `iter(x[, sentinel])` | 取迭代器 |
| `next(it[, default])` | 取下一个元素 |
| `map(f, *its)` | 惰性映射 |
| `filter(f, it)` | 惰性过滤 |
| `any(it)` / `all(it)` | 存在真值 / 全为真 |
| `slice(...)` | 切片对象（竞赛少用） |

### 字符与进制（7 个）

| 函数 | 作用 |
| --- | --- |
| `chr(i)` | 码点 → 字符，`chr(97)` → `'a'` |
| `ord(c)` | 字符 → 码点，`ord('a')` → 97 |
| `bin(n)` / `oct(n)` / `hex(n)` | 转二 / 八 / 十六进制串（**带前缀**） |
| `format(v, spec)` | 格式化，`format(11, "b")` → `"1011"`（无前缀） |
| `repr(x)` | 对象的调试表示 |
| `ascii(x)` | 同 `repr` 但非 ASCII 字符转义 |

### 反射与面向对象（15 个）

| 函数 | 作用 |
| --- | --- |
| `type(x)` | 类型对象 |
| `isinstance(x, T)` / `issubclass(A, B)` | 类型判断（考虑继承） |
| `id(x)` | 对象身份（CPython 里是地址） |
| `dir([x])` | 列出属性名 |
| `vars([x])` | 返回 `__dict__` |
| `getattr` / `setattr` / `delattr` / `hasattr` | 属性存取 |
| `callable(x)` | 是否可调用 |
| `super()` | 调用父类方法 |
| `property` / `staticmethod` / `classmethod` | 属性与方法装饰器 |
| `globals()` / `locals()` | 当前命名空间字典 |

### 输入输出与执行（8 个）

| 函数 | 作用 |
| --- | --- |
| `print(*obj, sep, end, file, flush)` | 输出 |
| `input([prompt])` | 读一行（**竞赛中不要传 prompt**） |
| `open(...)` | 打开文件（OJ 用 stdin/stdout，用不上） |
| `eval(s)` / `exec(s)` / `compile(...)` | 执行字符串代码 |
| `__import__(name)` | 动态导入 |
| `help(x)` | 交互式帮助（本地调试用） |

> **竞赛里几乎用不到的**：`memoryview`、`slice`、`compile`、`__import__`、`help`、
> `property`、`vars`、`dir`、`ascii`、`delattr`。看到知道是什么即可。
>
> **绝对不要在 OJ 上用 `eval` 解析输入**——它慢得离谱（要走一遍编译器），
> 而且遇到恶意/畸形数据会直接崩。解析数字永远用 `int()`。

---

## 2　竞赛高频 16 个详解

下表先给结论，后面逐个展开。**复杂度栏里的 $n$ 指输入规模**。

| 函数 | 复杂度 | 一句话 |
| --- | --- | --- |
| `len` | $O(1)$ | 所有内建容器都存了长度 |
| `sum` | $O(n)$ | 比手写循环快约 5 倍 |
| `max` / `min` | $O(n)$ | 支持 `key` 和 `default` |
| `sorted` | $O(n \log n)$ | Timsort，稳定 |
| `reversed` | $O(1)$ 建迭代器 | 不复制原序列 |
| `enumerate` | $O(1)$ 建 | 遍历时 $O(n)$ |
| `zip` | $O(1)$ 建 | 按最短的截断 |
| `map` | $O(1)$ 建 | 惰性；配内建函数最快 |
| `filter` | $O(1)$ 建 | 惰性 |
| `any` / `all` | $O(n)$ 最坏，**短路** | 传生成器才能真短路 |
| `abs` | $O(1)$ | 大整数为 $O(\text{位数})$ |
| `divmod` | $O(1)$ | 一次拿商和余数 |
| `pow(a,b,m)` | $O(\log b)$ 次模乘 | **内置快速幂，别手写** |
| `round` | $O(1)$ | 银行家舍入，慎用 |
| `range` | $O(1)$ | 对象不是列表 |
| `iter` / `next` | $O(1)$ | 手动驱动迭代 |

### `len(s)` — $O(1)$

所有内建容器（`list`/`tuple`/`str`/`dict`/`set`/`bytes`/`range`）都在对象头里存了长度，
**取长度永远是 $O(1)$**，不需要像 C 的 `strlen` 那样扫一遍。

生成器**没有** `len`，需要长度只能先 `list(...)`。

### `sum(iterable, start=0)` — $O(n)$

```python
sum(a)                       # 求和
sum(a, 100)                  # 从 100 开始加
sum(x * x for x in a)        # 传生成器，不建中间列表
sum(x > 0 for x in a)        # 布尔计数：统计正数个数
sum(row.count(1) for row in g)     # 二维计数
```

- **不要用 `sum` 拼接列表**：`sum(lists, [])` 是 $O(n^2)$，
  正确写法是 `list(itertools.chain(*lists))` 或 `[x for l in lists for x in l]`。
- `sum` 对 `float` 会累积误差，需要精确用 `math.fsum`。
- 求乘积没有内置函数，用 `math.prod(a)`（3.8+）。

### `max` / `min` — $O(n)$

三种调用形式：

```python
max(a)                       # 可迭代对象的最大元素
max(x, y, z)                 # 多个参数的最大值
max(a, key=len)              # 按 key 比较，**返回元素本身**
max(a, default=0)            # a 为空时返回 0，不抛异常
max(a, key=lambda p: p[1])   # 按第二维取最大的那个元素
```

> **两个坑**：
> 1. **空序列会抛 `ValueError`**。可能为空时一定写 `default=`。
> 2. `max(a, key=f)` 返回的是**元素**，不是 `f(元素)`。要最大的 key 值写 `max(map(f, a))`。

同时要最大值和它的下标：

```python
i = max(range(n), key=lambda i: a[i])         # 下标
mx, i = max((x, i) for i, x in enumerate(a))  # 值和下标（并列时取下标大的）
```

### `sorted(iterable, key=None, reverse=False)` — $O(n \log n)$

详见 [自定义排序](sorting.md)。这里只强调一点：
**`sorted` 接受任意可迭代对象，`list.sort` 只接受列表**。

```python
sorted(d.items(), key=lambda kv: -kv[1])      # 字典按值降序
sorted(s)                                     # 字符串 → 排好序的字符列表
"".join(sorted(s))                            # 字符串排序后再拼回去
```

### `reversed(seq)` — $O(1)$

返回**反向迭代器**，不复制数据：

```python
for x in reversed(a):        # ✅ 反向遍历，零额外内存
    ...
list(reversed(a))            # 需要列表时显式转换
a[::-1]                      # 切片，会复制一份，但对字符串更快
```

| 场景 | 推荐 |
| --- | --- |
| 只是反向遍历 | `reversed(a)` |
| 需要反转后的新列表 | `a[::-1]` |
| 反转字符串 | `s[::-1]`（`reversed` 返回的是字符迭代器，还要 `join`） |
| 原地反转列表 | `a.reverse()` |

`reversed` 要求对象支持 `__len__` + `__getitem__`（或 `__reversed__`），
**生成器和 `set` 不能 `reversed`**。

### `enumerate(iterable, start=0)` — 建 $O(1)$

```python
for i, x in enumerate(a):          # 从 0 开始
for i, x in enumerate(a, 1):       # 从 1 开始，处理 1-indexed 题目很方便
```

比 `range(len(a))` + `a[i]` 快 20%–30%（见
[条件与循环](control-flow.md#优化一enumerate-而不是-rangelena)）。

### `zip(*iterables)` — 建 $O(1)$

```python
for x, y in zip(a, b):                 # 并行遍历
list(zip(a, b))                        # [(a0,b0), (a1,b1), ...]
list(zip(*mat))                        # 转置：* 把每行拆成实参，zip 逐位取即得列
dict(zip(keys, values))                # 两个列表压成字典，按位置一一对应
for x, y in zip(a, a[1:]):             # 相邻元素对：a[1:] 是错开一位的同一序列
```

> **`zip` 按最短的截断，不报错**。长度不一致时静默丢数据，是隐蔽的 WA 来源。
> Python 3.10+ 有 `zip(..., strict=True)` 会报错，但 **3.9 没有**，只能自己 `assert len(a) == len(b)`。

`zip(*x)` 既能转置也能「解压」：

```python
pairs = [(1, 'a'), (2, 'b')]
nums, chs = zip(*pairs)                # (1, 2), ('a', 'b')
```

### `map(func, *iterables)` — 建 $O(1)$，惰性

```python
list(map(int, input().split()))        # ✅ 读整数的标准写法
a, b = map(int, input().split())       # 直接解包
list(map(str, a))                      # 转字符串
list(map(abs, a))                      # 逐元素取绝对值
list(map(max, a, b))                   # 多个序列并行：逐位取较大者
```

**`map` 只在配合「现成的 C 函数」时才快**：

| 写法 | 评价 |
| --- | --- |
| `map(int, tokens)` | ✅ 最快 |
| `map(str, a)` / `map(abs, a)` | ✅ 快 |
| `map(lambda x: x * 2, a)` | ❌ 比推导式慢 |
| `[x * 2 for x in a]` | ✅ 表达式用推导式 |

`map` 返回迭代器，**只能遍历一次**，且没有 `len`。

### `filter(func, iterable)` — 建 $O(1)$，惰性

```python
list(filter(None, a))                  # func 为 None 时过滤掉所有假值
list(filter(lambda x: x > 0, a))       # 不如推导式清晰
[x for x in a if x > 0]                # ✅ 推荐
```

竞赛里 `filter` 基本只有 `filter(None, ...)` 这一个惯用法值得记（去掉空串/0/None）。

### `any(iterable)` / `all(iterable)` — $O(n)$，短路

```python
any(x < 0 for x in a)                  # 存在负数
all(x > 0 for x in a)                  # 全是正数
any(g[i][j] == '#' for i in range(n) for j in range(m))
```

| 输入 | `any` | `all` |
| --- | --- | --- |
| 空序列 | `False` | **`True`**（数学上的「空真」） |
| 有真值 | `True`（**立刻停止**） | — |
| 有假值 | — | `False`（**立刻停止**） |

> **必须传生成器，不能传列表推导式**：
>
> ```python
> if any(check(x) for x in a):     # ✅ 找到第一个就停
> if any([check(x) for x in a]):   # ❌ 先把 n 个 check 全算完
> ```
>
> `all([])` 返回 `True` 这条也要记住，边界数据经常靠它。

### `abs(x)` — $O(1)$

```python
abs(-3)                      # 3
abs(-3.5)                    # 3.5
abs(3 + 4j)                  # 5.0，复数取模长
```

对大整数是 $O(\text{位数})$（要复制一份）。

### `divmod(a, b)` — $O(1)$

```python
q, r = divmod(17, 5)         # (3, 2)
divmod(-7, 2)                # (-4, 1)   ← 和 // 与 % 一致，向下取整
```

比分别写 `a // b` 和 `a % b` 快（只做一次除法）。数位分解的常用写法：

```python
digits = []
while n:                     # n 变成 0 说明所有位都取完了
    n, d = divmod(n, 10)     # 一次除法同时拿到「去掉末位的 n」和「末位 d」
    digits.append(d)         # 得到的是低位在前，需要高位在前就再 reverse
```

（不过 `list(map(int, str(n)))` 通常更快，因为全在 C 层。）

### `pow(base, exp[, mod])` — $O(\log \text{exp})$ 次乘法

**竞赛中最重要的内置函数之一。**

```python
pow(2, 10)                   # 1024
2 ** 10                      # 同上
pow(2, 100, 10 ** 9 + 7)     # ✅ 快速幂取模，C 实现
pow(a, MOD - 2, MOD)         # 费马小定理求逆元（MOD 为质数）
pow(a, -1, m)                # 模逆元，Python 3.8+ 直接支持
pow(2, 0.5)                  # 1.414...，指数可以是浮点
```

- **三参数 `pow` 比手写快速幂快 5–10 倍**，且中间值始终不超过 $\text{mod}^2$。
- 不带 `mod` 算 `pow(2, 10**6)` 会得到一个 30 万位的大整数，很慢，还可能 MLE。
- `math.pow` **只返回 `float`**，会丢精度且不支持三参数。别用。

详见 [快速幂与逆元](../math/number/inverse.md)。

### `round(x[, ndigits])` — $O(1)$

```python
round(3.7)                   # 4
round(2.5)                   # 2   ← 不是 3！
round(3.5)                   # 4
round(0.125, 2)              # 0.12
round(1234, -2)              # 1200，负数位数按十位/百位取整
```

Python 用的是**「四舍六入五成双」（banker's rounding）**，
外加浮点本身的二进制误差，`round` 在竞赛里**极不可靠**。

> 要严格的四舍五入，用 `decimal`：
>
> ```python
> from decimal import Decimal, ROUND_HALF_UP
> Decimal("2.5").quantize(Decimal("1"), rounding=ROUND_HALF_UP)     # 3
> ```
>
> 见 [浮点与科学计数法](../toolkit/float.md)。

`round(x)` 不带 `ndigits` 时返回 `int`，带了返回 `float`——这个类型差异也常引发问题。

### `range(start, stop, step)` — $O(1)$

见 [条件与循环](control-flow.md#4-range-的三个参数)。核心两点：
**左闭右开**、**是对象不是列表**（`x in range(...)` 是 $O(1)$）。

### `iter(x)` / `next(it[, default])` — $O(1)$

手动驱动迭代器，在「按需读取」的场景很有用：

```python
it = iter(sys.stdin.buffer.read().split())
n = int(next(it))                            # 读一个 token
a = [int(next(it)) for _ in range(n)]        # 读 n 个

first = next((x for x in a if x > 0), -1)    # 找第一个正数，没有则 -1
```

**`next` 一定要带默认值**，否则耗尽时抛 `StopIteration`。
`iter(callable, sentinel)` 的两参数形式竞赛用不上。

> 用迭代器代替「游标 + 下标」有两个好处：不用手动维护 `p`，而且 `next` 是 $O(1)$ 的 C 调用。
> 缺点是不能回退。数据格式简单时，迭代器写法更不容易错位。

---

## 3　几个特别容易搞混的对照

| 想做的事 | 正确写法 | 错误写法 |
| --- | --- | --- |
| 列表拼成字符串 | `"".join(map(str, a))` | `str(a)`（会带方括号和逗号） |
| 字符串转数字列表 | `list(map(int, s.split()))` | `list(s)`（得到字符） |
| 数字逐位拆开 | `list(map(int, str(n)))` | — |
| 二进制串（无前缀） | `format(n, "b")` | `bin(n)`（带 `0b`） |
| 整数平方根 | `math.isqrt(n)` | `int(n ** 0.5)`（大数丢精度） |
| 幂取模 | `pow(a, b, m)` | `a ** b % m`（先算出巨大中间值） |
| 求乘积 | `math.prod(a)` | `sum` 没有乘法版本 |
| 列表展平 | `[x for l in ls for x in l]` | `sum(ls, [])`（$O(n^2)$） |
| 严格四舍五入 | `Decimal(...).quantize(...)` | `round(x, k)` |
| 判断类型 | `isinstance(x, int)` | `type(x) == int`（忽略继承） |

---

## 4　例题

<!-- CHAPTER-EXAMPLE-TABLE -->

### BISHI21　【模板】排序（入门）

> 排序并输出长度 $n \le 10^5$ 的整数数组。
> 题面见 [原题](https://www.nowcoder.com/practice/40bf74658879460bbf5f1bfe772e8580)。

这题的价值在于**它整条流水线全是内置函数**，一个 Python 循环都没有：

```python
import sys


def main():
    data = sys.stdin.buffer.read().split()      # bytes 切成 token 列表
    a = sorted(map(int, data[1:]))              # map + sorted，全在 C 层
    sys.stdout.write(" ".join(map(str, a)) + "\n")


main()
```

四步四个内置函数：`split` → `map(int, ...)` → `sorted` → `map(str, ...)` + `join`。
$n = 10^5$ 时总耗时约 0.05 秒，其中排序只占 0.02 秒——**读入和输出才是大头**。

> **换成 Python 循环会怎样？**
>
> ```python
> a = []
> for tok in data[1:]:
>     a.append(int(tok))          # 慢约 2 倍
> ```
>
> 每一步都换成循环，总耗时会涨到 0.5 秒以上。这题时限宽松无所谓，
> 但 $n = 10^6$ 的题就是过与不过的区别。

### BISHI55　判断质数（入门）

> 给定 $n\ (1 \le n \le 10^{12})$，判断是否为质数，是输出 `Yes`，否则输出 `No`。
> 题面见 [原题](https://www.nowcoder.com/practice/9f418ff48b5e4e879f398352bed6118d)。

$n \le 10^{12}$ 意味着试除只需到 $\sqrt{n} = 10^6$。关键是**怎么算这个平方根**：

```python
import math


def main():
    n = int(input())
    if n < 2:                          # 1 和 0 都不是质数，必须单独挡掉
        print("No")
        return
    # 合数 n 至少有一个因子不超过 sqrt(n)，所以试除到 sqrt(n) 就足够；
    # +1 是因为 range 右端取不到，不加会漏掉 n 是完全平方数的情形
    for i in range(2, math.isqrt(n) + 1):
        if n % i == 0:                 # 找到真因子，立刻判定为合数
            print("No")
            return
    print("Yes")                       # 试除到底都没有因子


main()
```

三个要点：

- **用 `math.isqrt(n)`，别用 `int(n ** 0.5)`**。
  float 只有 53 位有效位（约 $9 	imes 10^{15}$），超过这个范围的整数转成 float 时先被舍入，
  开方结果可能比真值大、也可能比真值小：

  ```python
  math.isqrt(10 ** 18 - 1)         # 999999999      精确
  int((10 ** 18 - 1) ** 0.5)       # 1000000000     多算了 1
  ```

  本题 $n \le 10^{12}$ 恰好落在 53 位以内，`int(n ** 0.5)` 这次不会出错，
  但只要题目把上界抬到 $10^{16}$ 以上，同样的代码就会开始漏因子、把合数判成质数。
  `isqrt` 走的是纯整数牛顿迭代，没有浮点参与，任何规模都精确，速度也不慢——
  没有任何理由用浮点开方。这是本章「整数问题不用浮点」原则的典型。

- **`n < 2` 要特判**。$n = 1$ 不是质数，题目下界正好是 1，必踩。
- **循环上界是 `isqrt(n) + 1`**，因为 `range` 右开。少写 `+1` 会漏掉完全平方数
  （比如 $n = 4$ 会被判成质数）。

优化版（跳过偶数，常数减半）：

```python
def is_prime(n):
    if n < 2:
        return False
    if n < 4:
        return True                # 2, 3
    if n % 2 == 0:
        return False
    i = 3
    while i * i <= n:              # 用乘法比较，避免每次算 isqrt
        if n % i == 0:
            return False
        i += 2
    return True
```

$10^6$ 次循环在 Python 里约 0.3 秒，跳过偶数后约 0.15 秒，稳过。
更快的 Miller-Rabin 见 [整除分块与数论进阶](../math/number/sqrt-decomposition.md)。

### BISHI63　计算阶乘（简单）

> 给 $T\ (1 \le T \le 10^3)$ 个正整数 $n\ (1 \le n \le 10^6)$，
> 每个输出 $n! \bmod (10^9+7)$。
> 题面见 [原题](https://www.nowcoder.com/practice/b93729ad46d74a62801bdc320be2aa8e)。

朴素做法是每次查询循环乘 $n$ 次，最坏 $10^3 \times 10^6 = 10^9$，必然 TLE。
正解是**一次性预处理 $1! \sim 10^6!$ 的模阶乘表**，之后每次查询 $O(1)$：

```python
import sys

MOD = 10 ** 9 + 7
MAXN = 10 ** 6


def main():
    fac = [1] * (MAXN + 1)
    for i in range(1, MAXN + 1):
        fac[i] = fac[i - 1] * i % MOD          # 每步都取模

    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    out = [fac[int(data[1 + i])] for i in range(t)]
    sys.stdout.write("\n".join(map(str, out)) + "\n")


main()
```

要点：

- **绝对不要用 `math.factorial(n)`**。它算的是**精确值**：$10^6!$ 有约 $5.6 \times 10^6$ 位，
  计算要好几秒、内存要几十 MB，再取模也已经晚了。
  「先取模再运算」是整个数论部分的第一原则。
- **`fac[i-1] * i % MOD`** 的乘法中间值不超过 $10^9 \times 10^6 = 10^{15}$，
  C++ 得开 `long long`，Python 无所谓。
- **预处理的 $10^6$ 次循环是这题唯一的开销**，约 0.4 秒。
  这是「Python 循环上限 $10^7$/秒」经验值的实测：一次乘法 + 一次取模 + 一次列表写入，
  实测约 $2.5 \times 10^6$ 次/秒。
- 用 `itertools.accumulate` 可以把这个循环也搬到 C 层（见
  [标准库速查](stdlib.md#5-itertools)）：

  ```python
  from itertools import accumulate
  fac = [1] + list(accumulate(range(1, MAXN + 1),
                              lambda x, y: x * y % MOD))
  ```

  但因为 `lambda` 每步都是一次 Python 调用，实测**并不比朴素循环快**。
  `accumulate` 只有在用内置的 `operator.add`/`operator.mul` 时才有明显优势。
  这也说明一条：**「用了内置函数」不等于「快」，要看回调是不是 C 函数。**

完整题解：[BISHI21](../solutions/BISHI21.md)、[BISHI55](../solutions/BISHI55.md)、[BISHI63](../solutions/BISHI63.md)

---

## 5　本章速查

| 需求 | 内置函数 | 复杂度 |
| --- | --- | --- |
| 求和 | `sum(a)` | $O(n)$ |
| 最值 | `max(a, key=f, default=0)` | $O(n)$ |
| 排序 | `sorted(a, key=..., reverse=...)` | $O(n\log n)$ |
| 反向遍历 | `reversed(a)`（不复制） | $O(1)$ 建 |
| 下标 + 元素 | `enumerate(a, start)` | $O(1)$ 建 |
| 并行遍历 / 转置 | `zip(a, b)` / `zip(*mat)` | $O(1)$ 建 |
| 批量转换 | `map(int, tokens)` | $O(1)$ 建，惰性 |
| 存在 / 全部 | `any(gen)` / `all(gen)`，**短路** | $O(n)$ |
| 商和余数 | `divmod(a, b)` | $O(1)$ |
| 幂取模 | **`pow(a, b, m)`** | $O(\log b)$ |
| 模逆元 | `pow(a, m - 2, m)` 或 `pow(a, -1, m)` | $O(\log m)$ |
| 整数平方根 | `math.isqrt(n)`（不是内置但必须记） | $O(\log n)$ |
| 手动取元素 | `next(it, default)` | $O(1)$ |
| 字符 ↔ 码点 | `ord(c)` / `chr(i)` | $O(1)$ |
| 进制串 | `format(n, "b")`（无前缀） | — |

| 陷阱 | 说明 |
| --- | --- |
| `max([])` | 抛 `ValueError`，用 `default=` |
| `all([])` | 返回 `True` |
| `any([f(x) for x in a])` | 方括号会破坏短路 |
| `zip` 长度不等 | 静默截断，3.9 没有 `strict=` |
| `round(2.5)` | 得 2（银行家舍入），严格舍入用 `Decimal` |
| `sum(lists, [])` | $O(n^2)$，用推导式展平 |
| `math.pow` | 只返回 `float`，别用 |
| `eval` | 又慢又危险，解析数字用 `int()` |
| `map` / `filter` | 迭代器，只能遍历一次，没有 `len` |

# 附录 C　Python 算法竞赛避坑清单

> 这份清单按「后果严重程度 × 出现频率」排序。
> 带 ⚠️ 的是**会导致 WA/TLE 但不报错**的坑——它们最危险，因为你看不出哪里错了。
> 每条都注明了详细讲解所在章节。

---

## C.1　TLE 类（最高频）

### ⚠️ 1. `x in list` 是 $O(n)$

```python
seen = []
for x in a:
    if x not in seen:      # ← 整体 O(n²)，n=1e5 必 TLE
        seen.append(x)
```

**改用 `set`**。这是 Python 算法题最高频的 TLE 原因，没有之一。

> 判断方法：只要写出 `in` 且左边是循环变量，就停下来问一句——右边是 `set` 还是 `list`？
> 详见 [03-运算符与位运算 §3.5](../part1-python基础/03-运算符与位运算.md#35-成员与身份运算符)

### ⚠️ 2. `list.pop(0)` 是 $O(n)$

队列必须用 `collections.deque`。用 `list.pop(0)` 模拟队列，$n = 10^5$ 时退化成 $O(n^2)$。

反过来，`deque[i]` 随机访问也是 $O(n)$，**需要下标访问就别用 `deque`**。

> 详见 [33-队列与双端队列](../part3-数据结构/33-队列与双端队列.md)

### ⚠️ 3. 循环里拼接字符串是 $O(n^2)$

```python
s = ""
for x in a:
    s += str(x)            # ← 字符串不可变，每次都新建
```

改成 `"".join(map(str, a))`。

### 4. 逐行 `input()` / 逐次 `print()`

$10^5$ 行以上必须换成：

```python
data = sys.stdin.buffer.read().split()          # 读
sys.stdout.write("\n".join(out) + "\n")         # 写
```

实测十几倍差距。> 详见 [20-输入输出处理](../part2-竞赛基本功/20-输入输出处理.md)

### 5. 主逻辑写在模块级

包进 `def main():` 能快 20%–30%——局部变量走数组下标，全局变量走字典查找。

### ⚠️ 6. 大整数悄悄膨胀

Python 整数不会溢出，但会**越算越慢**。凡是循环里有 `*`、`<<`、`**` 而没取模的，
检查中间值会不会膨胀到几十万位：

```python
res = 1
for i in range(1, n + 1):
    res *= i               # ← n=1e6 时 res 有 550 万位，几分钟都算不完
print(res % MOD)

res = res * i % MOD        # ✅ 每步取模
```

C++ 里 `uint64` 溢出就自然截断了，Python 会老老实实一直算。

> 详见 [22-高精度与大整数 §22.2](../part2-竞赛基本功/22-高精度与大整数.md)

### 7. 递归调用开销

Python 函数调用比 C++ 贵一到两个数量级。递归 DP 能改递推就改递推。

---

## C.2　RE 类（运行时错误）

### 1. 递归深度

默认上限 **1000**。DFS 深度到 $10^5$ 必崩：

```python
sys.setrecursionlimit(300000)
```

但**改了也可能崩**——这只解除了解释器软限制，物理线程栈仍会段错误（判题机显示 RE）。稳妥做法：

```python
import threading
sys.setrecursionlimit(1 << 20)
threading.stack_size(1 << 26)      # 64 MB
t = threading.Thread(target=main); t.start(); t.join()
```

最彻底的是**改写成显式栈的迭代版本**。
> 详见 [60-DFS深度优先搜索](../part5-搜索/60-DFS深度优先搜索.md#604-递归改迭代)

### 2. 堆里存元组，比较到了不可比较的对象

```python
heappush(h, (dist, node_obj))      # dist 相等时会去比 node_obj → TypeError
heappush(h, (dist, idx, node_obj)) # ✅ 插一个唯一序号兜底
```

### 3. `int(s)` 的位数上限

Python 3.11+ 默认限制字符串转整数最多 4300 位。处理超长数字串时：

```python
try:
    sys.set_int_max_str_digits(0)
except AttributeError:             # 3.9/3.10 没有这个函数
    pass
```

### 4. 用内置函数名当变量

`sum`、`max`、`min`、`list`、`dict`、`set`、`id`、`input`、`str`、`type` 都不是关键字，
赋值不报错，但之后调用就 `TypeError: 'int' object is not callable`。

### 5. `from math import *` 覆盖内置 `pow`

`math.pow` 只返回 float，**没有三参数版本**，会让 `pow(a, b, mod)` 直接报错。
永远显式导入。

---

## C.3　WA 类（答案错误，最难查）

### ⚠️ 1. `round()` 和 `"%.nf"` 是银行家舍入

```python
>>> round(0.5), round(1.5), round(2.5), round(3.5)
(0, 2, 2, 4)                       # 不是 1,2,3,4
>>> "%.0f" % 2.5
'2'
```

题目要数学四舍五入时，**必须**用：

```python
from decimal import Decimal, ROUND_HALF_UP
Decimal(s).quantize(Decimal("0.000"), rounding=ROUND_HALF_UP)
```

**且必须从字符串构造 `Decimal`**——`Decimal(1.005)` 会先过一遍 float，拿到 `1.00499999...`，白搭。

> 详见 [23-浮点与科学计数法 §23.3](../part2-竞赛基本功/23-浮点与科学计数法.md)

### ⚠️ 2. `int(x ** 0.5)` 在大数上差 1

```python
>>> int(10 ** 18 ** 0.5)
>>> int((10 ** 18) ** 0.5)         # 999999999   ← 错了
>>> math.isqrt(10 ** 18)           # 1000000000  ← 对
```

判素数、找因子用 `int(n ** 0.5)` 当循环上界，会漏掉最后一个因子。**一律用 `math.isqrt`**。

### ⚠️ 3. `[[0] * m] * n` 的别名陷阱

```python
g = [[0] * m] * n          # n 行指向同一个列表！
g[0][0] = 1                # 每一行的第 0 个都变成了 1
g = [[0] * m for _ in range(n)]    # ✅
```

> 详见 [05-列表 §浅拷贝陷阱](../part1-python基础/05-列表.md#浅拷贝陷阱)

### ⚠️ 4. 位运算优先级低于比较运算符

```python
if x & 3 == 1:             # 实际是 x & (3 == 1) = x & False = 0
if (x & 3) == 1:           # ✅ 永远加括号
```

### 5. 可变默认参数

```python
def f(x, acc=[]):          # acc 在所有调用间共享！
def f(x, acc=None):
    if acc is None: acc = []       # ✅
```

### 6. 负数的 `//` 和 `%` 与 C++ 不同

| 表达式 | Python | C++ |
| --- | --- | --- |
| `-7 // 2` | `-4`（向下） | `-3`（向零） |
| `-7 % 2` | `1` | `-1` |

**好消息**：Python 取模对正模数恒非负，不需要 C++ 那样写 `((x % M) + M) % M`。
**坏消息**：需要向零截断时得自己处理。

### 7. `if not a` 无法区分空与零

`0`、`[]`、`""`、`None` 都是假值。当 `0` 是合法值时必须写 `if a is None`。

### 8. 浮点相等比较

永远用 `abs(x - y) < EPS`。实数二分用**固定 100 次迭代**而非 `while r - l > eps`。

### 9. `strip()` 与 `\r`

Windows 换行的输入文件会在行尾残留 `\r`，导致输出多一个不可见字符。
`input()` 只去掉 `\n`，字符串题记得 `.strip()`。

### 10. `str(list)` 不是拼接

```python
str([1, 2])                # "[1, 2]"  含方括号！
"".join(map(str, a))       # ✅
```

---

## C.4　题目理解类

### ⚠️ 1. Special Judge 题按样例比对会误判自己

题面写「若有多种答案，输出任意一个」时，你的输出和样例不同是**正常的**。
不要因此以为写错了。识别信号：

- 题面明说「输出任意一个」「若存在多个……」
- **两个示例的输入相同但输出不同**
- 题号或标题带 spj

### 2. 输入格式可能不统一

同一题的不同操作，每行的 token 数可能不同（例如查询操作不带参数）。
**按行读 + `split()` 后判长度**比 token 流游标更稳——后者依赖「某操作一定不带第二个数」这种
题面未必担保的假设，一旦某个测试点写法不同就会整体错位，且错得毫无征兆。

### 3. 输出描述里可能藏着输入信息

有的题把「本题有多组数据」写在**输出描述**里，输入描述完全没提。
**输入描述、输出描述、样例说明都要逐字读完**。

### 4. 题面渲染可能丢内容

牛客题面里的公式是图片，偶尔会渲染异常导致关键约束显示不全。
对不上样例时，回头核对题面是否完整——本项目就修过 5 道题的题面缺失
（含操作规则、左右孩子定义、核心约束整条丢失）。

---

## C.5　Python 打不过的题型

有些题即使算法完全正确，Python 也过不了。提前识别能省下大量时间：

| 信号 | 判断 |
| --- | --- |
| $n \ge 5\times10^5$ + 需要 $O(\log n)$ 区间数据结构 + 时限只有 C++ 的 2 倍 | 基本无解 |
| $O(n^2)$ 且 $n \ge 5000$ | $2.5\times10^7$ 次纯循环，超时 |
| 需要 $10^7$ 次以上 Python 层循环 | 超时（内置函数不算） |
| 递归线段树 $n = q = 10^5$ | 极险，改非递归或树状数组 |

**反过来，Python 占优的场景**：

| 场景 | 优势 |
| --- | --- |
| 大整数 / 高精度 | 原生支持，C++ 要写四套模板 |
| 精确分数、精确小数 | `fractions` / `decimal` |
| 排序 | `sorted` 是 C 实现的 Timsort，比手写快 50 倍 |
| 字符串处理 | 切片、`join`、`find` 全是 C 实现 |
| 位图 / 状态压缩 | 大整数位运算把循环压进 C 层，有时比降低渐进复杂度更有效 |

---

## C.6　优化决策树

TLE 时按顺序检查：

1. **复杂度对不对？** 先看数据规模反推该用什么复杂度。
2. **容器选对了吗？** `in` 用 `set`、队列用 `deque`、数组用 `list`。
3. **IO 快吗？** 换成 `buffer.read().split()` + `"\n".join`。
4. **循环能下沉到 C 层吗？** `sum`/`max`/`sorted`/`accumulate`/`Counter`/切片赋值。
5. **逻辑在函数里吗？** 包进 `main()`。
6. **热点变量绑成局部名了吗？** `push = res.append`。
7. **还是不行** → 这题可能就不该用 Python 做，见 C.5。

> **核心心法**：Python 优化不是让循环跑得更快，而是**让循环消失**。
> 详见 [21-复杂度与Python性能 §21.4](../part2-竞赛基本功/21-复杂度与Python性能.md)

---

## C.7　版本兼容速查

本教程全部代码兼容 **Python 3.9**。以下特性**不能用**（判题机版本未知时尤其要注意）：

| 特性 | 最低版本 | 3.9 的替代 |
| --- | --- | --- |
| `match` 语句 | 3.10 | `elif` 链 / 字典分派 |
| `int.bit_count()` | 3.10 | `bin(x).count("1")` |
| `itertools.pairwise` | 3.10 | `zip(a, a[1:])` |
| `bisect(..., key=)` | 3.10 | 预先构造键数组 |
| `zip(..., strict=True)` | 3.10 | 手动 `assert len(a) == len(b)` |
| `Counter.total()` | 3.10 | `sum(c.values())` |
| `sys.set_int_max_str_digits` | 3.11 | 包 `try/except AttributeError` |

**3.9 可以用的**（别误以为不能用）：`math.gcd` 多参数、`math.lcm`、`str.removeprefix/removesuffix`、
`dict |` 合并、`functools.cache`、`pow(a, -1, m)` 求逆元、`math.isqrt`、海象运算符 `:=`。

---

## C.8　牛客判题机相关

- **语言标识符是 `python3`**。`python` 在牛客的语言枚举里指的是 **Python 2**，选错会以 Py2 语法判题。
- **PyPy3 也可选**（标识符 `pypy3`），语法完全兼容 Python 3，速度快一个数量级，卡常题可以试。
- 未登录时页面上的 `window.supportLang` 字段恒为 `java,cpp`，**是占位符，没有参考价值**。
- 时限：题面写「C/C++ X 秒，其他语言 2X 秒」，Python 拿到的是双倍时限，但这远不足以抹平 20–50 倍的常数差距。
- 判题机**没有安装 `sortedcontainers`、`numpy` 等第三方库**，只能用标准库。

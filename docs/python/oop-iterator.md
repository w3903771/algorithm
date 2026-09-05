---
id: python/oop-iterator
title: 面向对象、迭代器与生成器
volume: 1
lang: py
---

# 第 15 章　面向对象与迭代器生成器

<!-- CHAPTER-EXAMPLES -->

笔试题里**很少需要写类**。但有三种情况绕不开：

1. 要把自定义对象放进 `sort` 或 `heapq` → 必须懂 **`__lt__`**。
2. 要把自定义对象当 `dict` 的键 / `set` 的元素 → 必须懂 **`__hash__` 和 `__eq__`**。
3. 要写「按需产生数据」的逻辑（分块读入、状态枚举）→ 必须懂 **生成器**。

本章按这个优先级组织：先把类讲够用，重点砸在魔术方法上，然后讲迭代器和生成器。

---

## 1　类与实例

```python
class Point:
    """二维点。"""

    cnt = 0                              # 类属性，所有实例共享

    def __init__(self, x, y):            # 构造函数（严格说是初始化函数）
        self.x = x                       # 实例属性
        self.y = y
        Point.cnt += 1

    def norm2(self):                     # 实例方法，第一个参数永远是 self
        return self.x * self.x + self.y * self.y


p = Point(1, 2)                          # 不需要 new
print(p.x, p.norm2(), Point.cnt)         # 1 5 1
```

和 C++ 的差异：

| 项 | C++ | Python |
| --- | --- | --- |
| 实例化 | `new Point(1,2)` / `Point p(1,2)` | `Point(1, 2)` |
| 成员访问 | 隐式 `this` | **显式 `self`**，且必须写在参数表第一位 |
| 成员声明 | 必须在类里声明 | 在 `__init__` 里赋值即创建，**随时能加新属性** |
| 访问控制 | `public/private/protected` | **只有约定**，没有强制 |
| 析构 | `~Point()` | `__del__`（靠引用计数，时机不确定，别依赖） |

### `self` 是什么

`self` 就是「当前实例」。**它不是关键字**，只是约定俗成的名字（写成 `this` 也能跑），
但**不能省略**：

```python
def norm2(self):        # ✅
def norm2():            # ❌ 调用 p.norm2() 时会 TypeError: takes 0 positional arguments but 1 was given
```

`p.norm2()` 实际被翻译成 `Point.norm2(p)`——**方法调用就是把实例作为第一个参数传进去**。

### 类属性 vs 实例属性

```python
class A:
    shared = []                          # 类属性，所有实例共享同一个列表！

    def __init__(self):
        self.own = []                    # 实例属性，每个实例一份


a, b = A(), A()
a.shared.append(1)
print(b.shared)                          # [1]   ← b 也看到了
a.own.append(1)
print(b.own)                             # []    ← 互不影响
```

> **和可变默认参数是同一个坑**：可变的类属性被所有实例共享。
> 需要每个实例独立的数据，**一律在 `__init__` 里用 `self.` 创建**。

赋值时的行为不对称：`a.shared = [9]` 会在实例上**新建**一个同名属性遮蔽类属性，
而 `a.shared.append(9)` 是就地改类属性。这个不对称很容易写出诡异 bug。

### 属性访问的私有约定

```python
class A:
    def __init__(self):
        self.pub = 1                     # 公开
        self._prot = 2                   # 约定「内部使用」，但外面照样能访问
        self.__priv = 3                  # 名称改写为 _A__priv，起到「防误用」作用
```

`__name`（**两个前导下划线、至多一个后置下划线**）会触发**名称改写**（name mangling），
被改成 `_类名__name`。它的目的是避免子类意外覆盖父类属性，**不是安全机制**。

竞赛里全部用公开属性即可，不要浪费时间搞封装。

---

## 2　`__slots__`：省内存又提速

默认每个实例都单独挂一个 `__dict__` 字典来存属性，
这样才能随时 `p.new_attr = 1` 加新字段。代价是每个实例都要养一张哈希表：
既有字典本身的固定开销，属性读写也要先算哈希再查槽位。

属性固定时声明 `__slots__`，解释器改用**固定槽位**存储——
每个属性在实例里占一个位置，类定义时就确定了偏移量，
既省掉整张字典，读写也变成直接按位置取，不再有哈希计算：

```python
class Node:
    __slots__ = ("val", "left", "right")

    def __init__(self, val):
        self.val = val
        self.left = None
        self.right = None
```

| 指标 | 无 `__slots__` | 有 `__slots__` |
| --- | --- | --- |
| 单个实例内存 | 约 150–200 字节 | 约 60–70 字节 |
| 属性读写速度 | 基准 | 快约 15%–20% |
| 能否动态加属性 | 能 | **不能** |

$n = 10^5$ 个节点时能省几十 MB，**建树 / 建图的题值得写**。

> 但更快的方案往往是**根本不建对象**：用并行数组（`left = [0]*n`、`right = [0]*n`）
> 或者 `list` 存元组。见 [链表](../ds/linked-list.md)。

---

## 3　继承

```python
class Base:
    def __init__(self, x):
        self.x = x

    def show(self):
        return "Base(%d)" % self.x


class Derived(Base):                     # 括号里写父类
    def __init__(self, x, y):
        super().__init__(x)              # 调用父类的 __init__，必须显式调用
        self.y = y

    def show(self):                      # 方法重写（override）
        return "Derived(%d, %d)" % (self.x, self.y)
```

要点：

- **父类的 `__init__` 不会自动调用**，必须写 `super().__init__(...)`。
  这是从 C++/Java 转过来最容易漏的一步。
- **所有方法都是「虚函数」**，不需要 `virtual` 关键字，重写即生效。
- 多继承按 **MRO**（方法解析顺序，C3 线性化）查找，`类名.__mro__` 可以查看。
  竞赛里不要用多继承。
- `isinstance(obj, Base)` 考虑继承，`type(obj) == Base` 不考虑。判类型用前者。

> **竞赛建议**：不要用继承。笔试题的对象模型简单到不需要它，
> 而每一层继承都会让属性查找多走一步 MRO，白白变慢。

---

## 4　魔术方法

「魔术方法」（magic method / dunder method）是**由语法或内建函数触发的特殊方法**。
下表按竞赛重要性排序：

| 方法 | 触发 | 竞赛重要性 |
| --- | --- | --- |
| **`__lt__(self, other)`** | `a < b`；**`sort` / `heapq` 只用它** | ★★★ |
| **`__eq__(self, other)`** | `a == b`；`in`、`dict` 查键 | ★★★ |
| **`__hash__(self)`** | `hash(a)`；作 `dict` 键 / `set` 元素 | ★★★ |
| **`__repr__(self)`** | `repr(a)`、直接 `print` 容器时 | ★★☆ |
| `__init__` | 实例化 | ★★★ |
| `__len__` | `len(a)`；也影响真值判断 | ★★☆ |
| `__iter__` / `__next__` | `for x in a` | ★★☆ |
| `__getitem__` / `__setitem__` | `a[i]`、`a[i] = v` | ★☆☆ |
| `__contains__` | `x in a` | ★☆☆ |
| `__str__` | `str(a)`、`print(a)` | ★☆☆ |
| `__call__` | `a(...)` | ☆☆☆ |
| `__add__` / `__sub__` / `__mul__` | `+` `-` `*` 运算符重载 | ☆☆☆ |

### `__lt__`：排序与堆的唯一入口

**Python 的 `sort` 和 `heapq` 只调用 `<`。** 不需要实现 `>`、`<=`、`>=`：
排序和堆要回答的问题只有一个——「这两个里哪个该排在前面」，一个 `<` 就够表达；
`a > b` 等价于 `b < a`，相等则是「两边都不小于对方」。
少写五个方法既省事，也杜绝了几个比较运算符互相矛盾的情况。

```python
import heapq


class Task:
    __slots__ = ("pri", "tid")

    def __init__(self, pri, tid):
        self.pri = pri
        self.tid = tid

    def __lt__(self, other):
        # 优先级降序；优先级相同则编号升序
        if self.pri != other.pri:
            return self.pri > other.pri
        return self.tid < other.tid

    def __repr__(self):
        return "Task(pri=%d, tid=%d)" % (self.pri, self.tid)


h = []
heapq.heappush(h, Task(3, 1))
heapq.heappush(h, Task(5, 2))
print(heapq.heappop(h))                  # Task(pri=5, tid=2)
```

> 想一次补齐六个比较运算符，用 `@functools.total_ordering` 装饰类
> （再实现 `__eq__` 即可）。**竞赛里只写 `__lt__` 就够。**

**如果没有 `__lt__` 会怎样？** 堆里存元组时，前面的项相等就会去比后面的对象：

```python
heapq.heappush(h, (dist, node_obj))      # dist 相等时会比较 node_obj → TypeError
heapq.heappush(h, (dist, idx, node_obj)) # ✅ 插一个唯一的 idx 做「打破平局」的键
```

这是堆相关题目最隐蔽的 RE 来源。**要么给类写 `__lt__`，要么保证元组的比较永远在对象之前分出胜负。**

### `__eq__` 与 `__hash__`：作字典键的两个必要条件

```python
class Point:
    __slots__ = ("x", "y")

    def __init__(self, x, y):
        self.x, self.y = x, y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))    # 直接复用元组的哈希，最省事也最可靠
```

三条硬规则：

1. **`a == b` 必须蕴含 `hash(a) == hash(b)`**。反之不必（哈希冲突是允许的）。
   违反这条会让 `dict`/`set` 静默出错——**查得到的键查不到**。
2. **只定义 `__eq__` 而不定义 `__hash__`，类会变成不可哈希的**
   （Python 自动把 `__hash__` 设为 `None`），放进 `set` 直接 `TypeError`。
3. **可变对象不要做键**。哈希值变了就再也找不回来了。

> **竞赛捷径：直接用元组当键。**
> `d[(x, y)] = v` 比自定义类快得多，也不会出错。
> 只有当「键」的语义特别复杂时才考虑写类——而笔试题基本不会这样。

### `__repr__`：调试神器

```python
def __repr__(self):
    return "Task(%d, %d)" % (self.pri, self.tid)
```

没有 `__repr__` 时，`print(列表)` 会输出一堆 `<__main__.Task object at 0x7f...>`，
调试时完全看不出内容。**只要写了类就顺手写 `__repr__`**，一行的事。

`__str__` 与 `__repr__` 的区别：`print(obj)` 优先用 `__str__`，
但 `print([obj])`（打印容器）**永远用 `__repr__`**。
只写一个的话，**写 `__repr__`**——它能兜底 `__str__`。

---

## 5　迭代器协议

一个对象能被 `for` 遍历，需要满足**迭代器协议**：

| 方法 | 职责 |
| --- | --- |
| `__iter__(self)` | 返回一个**迭代器**（通常是 `self` 或一个新对象） |
| `__next__(self)` | 返回下一个元素；没有了就 `raise StopIteration` |

```python
class Countdown:
    def __init__(self, n):
        self.n = n

    def __iter__(self):
        return self

    def __next__(self):
        if self.n <= 0:
            raise StopIteration
        self.n -= 1
        return self.n + 1


for x in Countdown(3):
    print(x)                             # 3 2 1
```

`for x in obj` 实际展开成：

```python
it = iter(obj)                           # 调 obj.__iter__()
while True:
    try:
        x = next(it)                     # 调 it.__next__()
    except StopIteration:
        break
    ...
```

### 「可迭代对象」与「迭代器」不是一回事

| 概念 | 需要的方法 | 例子 | 能遍历几次 |
| --- | --- | --- | --- |
| 可迭代对象（iterable） | `__iter__` | `list`、`str`、`dict`、`range` | **多次** |
| 迭代器（iterator） | `__iter__` + `__next__` | `map`、`filter`、`zip`、生成器、文件对象 | **一次** |

```python
a = [1, 2, 3]
sum(a); sum(a)                           # 6, 6      列表可以反复遍历
m = map(int, "123")
sum(m); sum(m)                           # 6, 0      迭代器耗尽后是空的
```

> **竞赛里最常见的表现**：
>
> ```python
> data = map(int, sys.stdin.read().split())
> n = next(data)
> a = list(data)                          # ✅ 转成列表后就能反复用
> ```
>
> 如果直接把 `map` 对象存起来当数组用，第二次访问就是空的。
> **凡是要用两次的，先 `list(...)`。**
>
> 原因是迭代器内部只有一个**向前走的游标**，既不保存已产出的元素，也没有回退操作。
> 走到头之后再要元素，它只能立刻抛 `StopIteration`——
> 于是 `sum` 收到零个元素，安静地返回 0 而不是报错。这种「静默变空」正是它难查的地方。

---

## 6　生成器与 `yield`

把函数里的 `return` 换成 `yield`，函数就变成**生成器函数**——
调用它不执行函数体，而是返回一个生成器对象；每次 `next` 才执行到下一个 `yield` 并暂停。

```python
def fib(n):
    a, b = 1, 1
    for _ in range(n):
        yield a                          # 产出一个值，然后「冻结」在这里
        a, b = b, a + b


for x in fib(5):
    print(x)                             # 1 1 2 3 5
```

生成器**自动实现了迭代器协议**，比手写 `__iter__`/`__next__` 短得多，
而且状态（局部变量、执行位置）由解释器自动保存。

### `yield from`

```python
def flatten(nested):
    for item in nested:
        if isinstance(item, list):
            yield from flatten(item)     # 委托给子生成器，等价于 for x in ...: yield x
        else:
            yield item


list(flatten([1, [2, [3, 4]], 5]))       # [1, 2, 3, 4, 5]
```

### 生成器表达式 vs 生成器函数

```python
g = (x * x for x in a)                   # 生成器表达式，简单变换用它
def g():                                 # 生成器函数，逻辑复杂时用它
    for x in a:
        if check(x):
            yield transform(x)
```

两者产生的是同一种对象（生成器），区别只在能写多复杂的逻辑：
表达式里塞不下多条语句，一旦需要临时变量、多层分支或提前结束，就得改写成生成器函数。

---

## 7　生成器在竞赛里的用途与陷阱

### 三个真实用途

**1. 省内存的大规模遍历。**

```python
# 枚举 10^7 个状态，只关心是否存在满足条件的
if any(check(s) for s in gen_states()):
    ...
```

**2. 按需读入 token。**

```python
import sys


def tokens():
    for line in sys.stdin:               # 逐行读，任何时刻内存里只有一行
        for tok in line.split():
            yield tok                    # 交出一个 token 就地冻结，下次 next 再从这里继续


it = tokens()
n = int(next(it))                        # 手动取一个：开头的 n
a = [int(next(it)) for _ in range(n)]    # 接着往下取 n 个，游标自动接续，不会重复
```

比一次性 `read().split()` 省内存，适合输入极大（几百 MB）的题。
不过多数情况下 `read().split()` 更快，**除非内存真的吃紧**。

**3. 递归改迭代时保存状态。**
用生成器模拟递归可以绕开递归深度限制，但写法复杂，
一般直接用显式栈更好（见 [DFS深度优先搜索](../search/dfs.md)）。

### 五个陷阱

> **陷阱 1：只能遍历一次。** 最高频的错误。
>
> ```python
> g = (x for x in a if x > 0)
> print(max(g))            # 正常
> print(sum(g))            # 0，已经耗尽
> ```

> **陷阱 2：没有 `len`，不能索引，不能切片。**
> `len(g)`、`g[0]`、`g[1:3]` 全部报错。要取前 $k$ 个用 `itertools.islice(g, k)`。

> **陷阱 3：惰性求值让异常「迟到」。**
>
> ```python
> g = (10 // x for x in [1, 0, 2])
> # 这一行不报错
> list(g)                  # 这里才 ZeroDivisionError
> ```
>
> 调试时表现为「报错行号和真正的问题位置对不上」。

> **陷阱 4：一半立即求值，一半惰性求值。**
>
> ```python
> a = [1, 2, 3]
> g = (x * k for x in a)   # 创建时就取走了 a 这个对象，但 k 还没求值
> a = [9, 9, 9]            # 重新绑定 a，对 g 无效
> k = 10                   # k 在「消费」时才被读取
> list(g)                  # [10, 20, 30]
> ```
>
> 精确规则：**最外层 `for` 后面的可迭代对象在创建生成器时立即求值，
> 表达式和 `if` 条件里的其它名字都要到消费时才读取**。
> 见 [推导式](comprehension.md#生成器表达式的第一个可迭代对象是立即求值的)。

> **陷阱 5：生成器比列表慢（单次遍历时）。**
> 每次 `next` 都要恢复/保存帧状态。$n$ 不大（$\le 10^6$）且要多次访问时，
> **直接建列表更快**。生成器的价值是省内存和短路，不是速度。

---

## 8　竞赛里到底该不该写类？

| 场景 | 建议 |
| --- | --- |
| 存一组固定字段的数据 | **用元组**，`(score, sid)` |
| 需要按多关键字排序 | **用元组 + `key`**，见[自定义排序](sorting.md) |
| 需要放进 `dict`/`set` | **用元组**（天然可哈希） |
| 需要多个字段且要可读 | `namedtuple`（慢一点但清晰） |
| 树/图节点，$n \le 10^5$ | 类 + `__slots__`，或**并行数组**（更快） |
| 树/图节点，$n \ge 10^6$ | **一定用并行数组**，类的对象开销撑不住 |
| 需要自定义比较规则且到处复用 | 类 + `__lt__` |

> **一句话**：Python 竞赛里 90% 的「对象」都应该是元组。
> 写类的唯一强理由是「需要自定义 `__lt__` 且用在多处」。

---

## 9　例题：BISHI6 【模板】整数优先队列

<!-- CHAPTER-EXAMPLE-TABLE -->

> 空多重集合，$n\ (1 \le n \le 10^6)$ 个操作：`1 x` 插入、`2` 输出最小值、`3` 删除最小值。
> 题面见 [原题](https://www.nowcoder.com/practice/a88e9711f7b04369982bbe8902278ae4)。

标准解法在 [标准库速查](stdlib.md#11-例题) 已给出，
这里从**面向对象**的角度补三点。
（下面沿用那份题解的快读与游标写法，读入方式本身见 [输入输出处理](../toolkit/io.md)。）

### 元素是 `int`，所以什么都不用写

```python
import sys
from heapq import heappush, heappop


def main():
    data = sys.stdin.buffer.read().split()
    p = 0                                # p 是 token 流的游标，手动推进
    n = int(data[p]); p += 1
    h = []                               # heapq 直接拿普通 list 当小根堆用，不需要包装类
    out = []
    for _ in range(n):
        # 操作 2、3 后面没有参数，游标只能读到 op 之后再决定要不要多走一格
        op = data[p]; p += 1
        if op == b"1":
            heappush(h, int(data[p])); p += 1
        elif op == b"2":
            out.append(h[0])             # 小根堆最小值恒在下标 0，取它是 O(1) 且不改动堆
        else:
            heappop(h)
    sys.stdout.write("\n".join(map(str, out)) + "\n")


main()
```

`int` 自带 `__lt__`，堆直接能用。**这题最好的「面向对象设计」就是不设计。**

### 如果元素带附加信息呢

假设题目改成「插入 `(值, 编号)`，按值取最小，值相同取编号小的」，有两种写法：

```python
# 写法一：元组（推荐）
heappush(h, (val, idx))                  # 元组的 __lt__ 是字典序，天然满足要求

# 写法二：自定义类
class Item:
    __slots__ = ("val", "idx")

    def __init__(self, val, idx):
        self.val, self.idx = val, idx

    def __lt__(self, other):
        if self.val != other.val:
            return self.val < other.val
        return self.idx < other.idx


heappush(h, Item(val, idx))
```

$n = 10^6$ 时，**写法一快约 3 倍、省约 4 倍内存**。
只有当比较规则复杂到元组表达不了（比如「值降序 + 名字降序」，名字是字符串取不了负）
才值得写类。

### 这题为什么不该自己实现堆

「模板题」听起来像是要手写二叉堆。**别写**：

| 实现 | $n = 10^6$ 的耗时 |
| --- | --- |
| `heapq`（C 实现） | 约 2–3 秒 |
| 手写 Python 二叉堆（列表 + 上浮下沉） | 约 20–40 秒 |

差 10 倍以上。手写堆的原理必须懂（见
[优先队列与堆](../ds/heap.md)），但**提交的代码永远用 `heapq`**。

完整题解：[`solutions/nowcoder/BISHI6/sol.py`](../solutions/BISHI6.md)

---

## 10　本章速查

| 要点 | 结论 |
| --- | --- |
| `self` | 必须显式写在参数表第一位，不是关键字 |
| 实例属性 | 在 `__init__` 里 `self.x = ...` 创建 |
| **可变类属性** | 被所有实例共享，和可变默认参数是同一个坑 |
| 父类初始化 | **不会自动调用**，要写 `super().__init__(...)` |
| 继承 | 竞赛里不要用 |
| `__slots__` | 属性固定时写，省 2/3 内存、快 15%–20% |
| **`sort` / `heapq`** | **只调用 `__lt__`**，其它比较方法可以不写 |
| 堆里存元组 | 前几项相等会比到后面的对象，**加一个唯一序号打破平局** |
| 作 `dict` 键 | 必须同时有 `__eq__` 和 `__hash__`，且 `a == b ⟹ hash 相同` |
| 只写 `__eq__` | 类变成不可哈希，进 `set` 会 `TypeError` |
| `__hash__` 实现 | `return hash((self.x, self.y))`，复用元组哈希 |
| `__repr__` | 只要写类就顺手写，否则调试看不到内容 |
| 迭代器协议 | `__iter__` 返回迭代器，`__next__` 结束时 `raise StopIteration` |
| 可迭代 vs 迭代器 | `list` 能遍历多次，`map`/`zip`/生成器**只能一次** |
| 要用两次 | 先 `list(...)` |
| 生成器 | `yield` 暂停并保存状态；`yield from` 委托子生成器 |
| 生成器的价值 | **省内存 + 短路**，不是速度 |
| 生成器陷阱 | 一次性、无 `len`、无索引、异常延迟到消费时 |
| 竞赛对象设计 | **90% 的情况用元组**，只有需要自定义 `__lt__` 时才写类 |
| 手写数据结构 | 原理要懂，提交的代码用 `heapq` / `deque`（C 实现快 10 倍） |

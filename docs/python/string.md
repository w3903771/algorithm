---
id: python/string
title: 字符串
volume: 1
lang: py
---

# 第 4 章　字符串

<!-- CHAPTER-EXAMPLES -->

字符串是笔试里出现频率最高的数据类型——输入是字符串、输出是字符串、一半的题面本身就在讲字符串。

从 C++ 转过来要先记住一条：**Python 的 `str` 是不可变的**。
它不是 `std::string`（可以 `s[0] = 'x'`），而更像 Java 的 `String`。
这一条决定了本章后半段几乎所有的性能讨论。

---

## 1　字面量与转义

### 四种引号

```python
s1 = 'single'
s2 = "double"                   # 单双引号完全等价，没有 char/string 之分
s3 = '''三引号
可以跨行'''
s4 = """三引号
也可以用双引号"""
```

Python **没有字符类型**。`'a'` 就是一个长度为 1 的字符串，`s[0]` 拿到的也是长度为 1 的字符串。
这跟 C++ 的 `char` 是完全不同的东西——见 §7 的 `ord`/`chr`。

选单引号还是双引号的唯一标准是**哪个能少写转义**：

```python
print("it's ok")                # 不用转义
print('he said "hi"')           # 不用转义
```

### 转义字符表

| 转义 | 含义 | 竞赛中的用处 |
| --- | --- | --- |
| `\n` | 换行 | `"\n".join(...)` 拼接输出 |
| `\t` | 制表符 | 少数题目要求 Tab 分隔 |
| `\\` | 反斜杠本身 | 路径、正则 |
| `\'` `\"` | 引号 | 引号冲突时 |
| `\r` | 回车 | **Windows 换行残留，见下面的坑** |
| `\0` | 空字符 | 几乎用不到 |
| `\xhh` | 十六进制字符 | `"\x41"` 就是 `"A"` |
| `\ooo` | 八进制字符 | `"\101"` 就是 `"A"` |
| 行尾 `\` | 续行 | 见 [语法与执行模型](syntax.md) |

> **`\r` 是 OJ 上最阴的 WA 来源**。如果测试数据是 Windows 格式（`\r\n`），
> `input()` 只去掉 `\n`，留下的 `\r` 会跟着答案一起输出，肉眼看不见但评测机看得见。
> **读进来的字符串一律 `.strip()` 或 `.rstrip()`**，代价可以忽略。

### 原始字符串 r"..."

前缀 `r` 让反斜杠失去转义能力：

```python
print(r"\n")                    # 输出两个字符：反斜杠和 n
print("\n")                     # 输出一个换行
```

竞赛里基本只在写正则时用得上（`re.compile(r"\d+")`）。
注意 `r"..."` **不能以奇数个反斜杠结尾**，`r"\"` 是语法错误。

### 字符串拼接的字面量特性

**相邻的字符串字面量会在编译期自动拼接**，这是写长提示串的惯用法：

```python
msg = ("这是一段很长的话，"
       "写成两行更好读，"
       "运行时它们是一个字符串")
```

注意这只对**字面量**成立，变量之间必须用 `+`。

---

## 2　索引与切片

索引与 C++ 一样从 0 开始，但 Python 额外支持**负索引**（从末尾数，`-1` 是最后一个）：

```
 s =   P   y   t   h   o   n
正索引 0   1   2   3   4   5
负索引-6  -5  -4  -3  -2  -1
```

```python
s = "Python"
s[0]        # 'P'
s[-1]       # 'n'      ← 取最后一个字符，不用写 s[len(s)-1]
s[6]        # IndexError: string index out of range
```

### 切片 `s[start:stop:step]`

切片是 Python 最重要的语法之一，**永远左闭右开**，且**越界不报错**：

```python
s = "abcdefg"
s[1:4]      # 'bcd'     [1, 4)
s[:3]       # 'abc'     省略 start = 0
s[3:]       # 'defg'    省略 stop = len(s)
s[:]        # 'abcdefg' 完整副本
s[-3:]      # 'efg'     最后三个
s[:-3]      # 'abcd'    去掉最后三个
s[::2]      # 'aceg'    步长 2
s[::-1]     # 'gfedcba' ← 反转字符串的标准写法
s[100:200]  # ''        越界不报错，返回空串
```

| 需求 | 写法 |
| --- | --- |
| 反转 | `s[::-1]` |
| 去掉首尾各一个字符 | `s[1:-1]` |
| 前 $k$ 个 | `s[:k]` |
| 后 $k$ 个 | `s[-k:]`（注意 $k=0$ 时会返回**整串**！） |
| 每隔一个取 | `s[::2]` |
| 判断回文 | `s == s[::-1]` |

> **`s[-k:]` 在 `k == 0` 时是 `s[0:]`，也就是整个串**，不是空串。
> 需要「取最后 k 个，k 可能为 0」时写 `s[len(s) - k:]`。

**切片的复杂度是 $O(\text{切片长度})$**，因为它复制。
在循环里反复 `s[i:j]` 是隐蔽的 $O(n^2)$：

```python
# ❌ 每次切片都复制，总复杂度 O(n²)
for i in range(n):
    if s[i:i + m] == t:
        ...

# ✅ 用 find / 或者哈希，见第 36、71 章
pos = s.find(t)
```

---

## 3　字符串是不可变的

```python
s = "abc"
s[0] = "x"          # ❌ TypeError: 'str' object does not support item assignment
```

要「修改」只能造新串：

```python
s = "x" + s[1:]                     # 换第一个字符
a = list(s); a[0] = "x"; s = "".join(a)   # 需要多处修改时先转 list
```

> **需要频繁按下标改字符时，先 `a = list(s)` 变成字符列表，改完再 `"".join(a)`**。
> 这是竞赛里处理字符串修改的标准套路：`list` 可变、$O(1)$ 随机写，`join` 一次 $O(n)$ 收尾。

### 循环拼接是 $O(n^2)$ 陷阱

这是 Python 算法题的**第二大 TLE 来源**（第一是 `in list`，见 [运算符与位运算](operators.md#5-成员与身份运算符)）：

```python
# ❌ 每次 += 都要新建一个字符串并复制全部已有内容
res = ""
for x in a:
    res += str(x) + " "
```

第 $i$ 次拼接复制 $i$ 个字符，总代价 $1 + 2 + \dots + n = O(n^2)$。
$n = 10^5$ 时是 $5 \times 10^9$ 次字符复制，必然 TLE。

正确写法是**先收集到列表，最后 `join` 一次**：

```python
# ✅ O(总长度)
parts = []
for x in a:
    parts.append(str(x))
res = " ".join(parts)

# ✅ 更短
res = " ".join(map(str, a))
```

`join` 会先遍历一遍算出总长度，一次性分配内存，然后逐段拷贝，总复杂度 $O(\sum |s_i|)$。

> **有人会说「CPython 对 `s += t` 做了原地扩容优化，实测不慢」**——这是真的，
> 但**只在 `s` 的引用计数为 1 时生效**。一旦把中间结果存进列表、传给函数、或者换成 PyPy，
> 优化立刻失效，退化回 $O(n^2)$。这种「看运气」的性能不能依赖。
>
> 记住结论：**任何时候拼接字符串都用 `join`，没有例外。**

同理，输出大量行时不要在循环里 `print`：

```python
sys.stdout.write("\n".join(out) + "\n")     # 见 20 章
```

---

## 4　字符串方法全表

Python 的 `str` 有 40 多个方法，**全部返回新串，绝不修改原串**。
按用途分成六类，竞赛高频的用 ★ 标出。

> **先说签名里的方括号。** 下面的表格用的是官方文档的记法：
> **方括号括起来的参数是可选的，方括号本身不是要敲进去的字符**。
>
> | 签名 | 合法的调用 |
> | --- | --- |
> | `s.center(w[, c])` | `s.center(9)`、`s.center(9, "*")` |
> | `s.replace(old, new[, cnt])` | `s.replace("a", "X")`、`s.replace("a", "X", 1)` |
> | `s.find(t[, b[, e]])` | `s.find("bc")`、`s.find("bc", 2)`、`s.find("bc", 2, 6)` |
>
> 所以 `"abc".center(9, "*")` 与签名 `s.center(w[, c])` 并不矛盾——
> 它就是「带上可选参数 `c`」的那种调用。
>
> **方括号套方括号表示「外层给了才能给内层」**：`s.find(t[, b[, e]])` 里的 `e`
> 嵌在 `b` 的括号内，意思是可以只给 `b`、也可以 `b` 和 `e` 都给，
> 但**不能只给 `e` 不给 `b`**——位置参数是按顺序对上的，跳不过去。
> 全书的方法签名都按这个记法写。

### 查找与定位

| 方法 | 作用 | 找不到时 |
| --- | --- | --- |
| ★ `s.find(t[, b[, e]])` | 在切片 `s[b:e]` 里找 `t` 首次出现的下标 | 返回 `-1` |
| `s.rfind(t[, b[, e]])` | 从右找 | 返回 `-1` |
| `s.index(t[, b[, e]])` | 同 `find` | **抛 `ValueError`** |
| `s.rindex(t[, b[, e]])` | 同 `rfind` | 抛 `ValueError` |
| ★ `s.count(t)` | `t` 出现次数（**不重叠**） | 返回 `0` |
| ★ `t in s` | 是否包含 | 返回 `False` |
| ★ `s.startswith(t)` | 是否以 `t` 开头，参数可以是元组 | |
| ★ `s.endswith(t)` | 是否以 `t` 结尾，参数可以是元组 | |

```python
s = "abcabc"
s.find("bc")            # 1
s.rfind("bc")           # 4
s.find("bc", 2)         # 4      从下标 2 开始找
s.count("abc")          # 2
"aaaa".count("aa")      # 2      ← 不重叠！不是 3
s.startswith(("ab", "xy"))      # True   参数可以是元组，等于「或」
```

**`b` 与 `e` 是搜索范围的起止下标**，语义与切片 `s[b:e]` 完全一致：
左闭右开，省略 `b` 是从 0 开始，省略 `e` 是找到串尾。

```python
s = "abcabc"
s.find("bc", 2)         # 4      只在 s[2:] 里找
s.find("bc", 2, 6)      # 4      s[2:6] = "cabc"，命中，返回的是原串下标 4
s.find("bc", 2, 5)      # -1     s[2:5] = "cab"，右端是开区间，"bc" 放不下
```

**返回的下标是相对原串 `s` 的，不是相对切片的。** 只在**找得到**的时候，
`s.find(t, b)` 才与 `s[b:].find(t) + b` 相等；找不到时两者会分道扬镳：

```python
s = "abcabc"
s.find("zz", 2)             # -1     找不到就是 -1，与 b 无关
s[2:].find("zz") + 2        # 1      ← -1 + 2，一个看着完全合法的下标
```

后一种写法把「没找到」的哨兵值 `-1` 也平移了 `b`，于是错误被伪装成正常结果。
**要限定搜索范围就传 `b`/`e`，不要先切片再补偏移。**

传下标还有一个好处是**不复制字符串**：切片是 $O(e-b)$ 的拷贝，传下标是 $O(1)$。
在循环里反复搜索时差别很大：

```python
# 找出 t 的全部出现位置（可重叠）：游标写法，全程不切片
pos, i = [], s.find(t)
while i != -1:
    pos.append(i)
    i = s.find(t, i + 1)        # 从上一次命中的下一位继续找
```

**`index` 与 `find` 只差在「找不到时怎么办」**：`find` 返回 `-1`，`index` 抛
`ValueError`。功能、复杂度、参数全都一样。

竞赛里**默认用 `find`**：结果要么是合法下标要么是 `-1`，一个 `if` 就能分流，
不需要 `try`。反过来说，只有在「找不到就是数据出错、应该当场炸掉」时才用 `index`。

`find` 的坑是 **`-1` 本身是合法的负下标**，直接拿去索引不会报错，而是悄悄取到最后一个字符：

```python
i = s.find(t)
c = s[i]                # ❌ 没找到时 i = -1，这里取到的是 s[-1]，不报错但结果全错
if i != -1:             # ✅ 用 find 就必须显式判 -1
    c = s[i]
```

> `count` 统计的是**不重叠**出现次数。求重叠出现次数要自己写循环或用 KMP，
> 见 [字符串匹配KMP](../string/kmp.md)。

### 判定（全是 `is*`，返回 bool）

| 方法 | 含义 | 空串时 |
| --- | --- | --- |
| ★ `s.isdigit()` | 全是数字字符（含 `²` 这类上标） | `False` |
| `s.isdecimal()` | 全是十进制数字（最严格） | `False` |
| `s.isnumeric()` | 全是数值字符（含 `½`、汉字「一」） | `False` |
| ★ `s.isalpha()` | 全是字母（含汉字） | `False` |
| ★ `s.isalnum()` | 全是字母或数字 | `False` |
| `s.islower()` / `s.isupper()` | 全小写 / 全大写 | `False` |
| `s.isspace()` | 全是空白 | `False` |
| `s.istitle()` | 是否每个单词首字母大写 | `False` |
| `s.isascii()` | 全是 ASCII（3.7+） | **`True`** |

```python
"²".isdigit()       # True   ← 上标 2 也算 digit
"²".isdecimal()     # False  ← 但不是 decimal
"½".isnumeric()     # True
"一".isnumeric()    # True   ← 汉字数字
"-5".isdigit()      # False  ← 负号不是数字！
```

> **`"-5".isdigit()` 是 `False`**。想判断「这个 token 是不是合法整数」，
> 老老实实 `try: int(s) except ValueError:`，不要用 `isdigit`。
> 另外要严格判十进制阿拉伯数字请用 `isdecimal`，`isdigit` 会放过全角/上标字符。

### 大小写转换

| 方法 | 作用 |
| --- | --- |
| ★ `s.lower()` / `s.upper()` | 全转小写 / 大写 |
| `s.capitalize()` | 首字母大写，其余小写 |
| `s.title()` | 每个单词首字母大写 |
| `s.swapcase()` | 大小写互换 |
| `s.casefold()` | 比 `lower()` 更激进的折叠（处理德语 ß 等） |

```python
"hello world".title()       # 'Hello World'
"hello".capitalize()        # 'Hello'
"Hello".swapcase()          # 'hELLO'
```

大小写不敏感的比较统一写 `a.lower() == b.lower()`。

### 修剪与填充

| 方法 | 作用 |
| --- | --- |
| ★ `s.strip([chars])` | 去掉**首尾**指定字符集（默认空白） |
| ★ `s.lstrip()` / `s.rstrip()` | 只去左 / 只去右 |
| ★ `s.zfill(w)` | 左补 `0` 到宽度 `w`，**正确处理负号** |
| `s.ljust(w[, c])` / `s.rjust(w[, c])` | 左 / 右对齐填充到宽度 `w`，补 `c` |
| `s.center(w[, c])` | 居中填充到宽度 `w`，补 `c` |
| `s.expandtabs(n)` | Tab 展开成空格 |
| `s.removeprefix(p)` / `s.removesuffix(p)` | 去掉前缀 / 后缀（**3.9+**） |

```python
"  hi  ".strip()            # 'hi'
"xxhixx".strip("x")         # 'hi'     ← 参数是字符集合，不是子串
"ab".zfill(5)               # '000ab'
"-12".zfill(6)              # '-00012' ← 负号留在最前面
"abc".center(9, "*")        # '***abc***'
```

`ljust` / `rjust` / `center` 三个方法的参数含义相同：

- **`w` 是补完之后的总宽度**，不是「补几个」。原串已经不短于 `w` 时原样返回，
  **绝不截断**。
- **`c` 是拿来补位的那一个字符**，可选，默认是空格。必须正好一个字符，
  给多给少都是 `TypeError`。

```python
"abc".center(9)             # '   abc   '   ← 省略 c，默认补空格
"abc".center(9, "*")        # '***abc***'   ← 用 * 补
"abc".center(2, "*")        # 'abc'         ← 宽度不够，原样返回而不是截断
"abc".ljust(6, "-")         # 'abc---'
"abc".rjust(6, "-")         # '---abc'
"abc".center(10, "*")       # '***abc****'  ← 补不平时右边多一个
```

`zfill(w)` 相当于 `rjust(w, "0")`，唯一的区别是它**认识正负号**：
`"-12".zfill(6)` 是 `'-00012'`，而 `"-12".rjust(6, "0")` 是 `'000-12'`。
补前导零一律用 `zfill`。

> **`strip("abc")` 去掉的是「首尾所有属于 {a,b,c} 的字符」，不是去掉子串 `"abc"`**。
> 想去前缀用 `removeprefix`（3.9+）或切片。这是极高频的误用。

两者的差别，一句话是**「按字符集反复剥」对「按子串剥一次」**：

```python
"abcHELLOcba".strip("abc")      # 'HELLO'      首尾凡是 a/b/c 就一直剥，顺序无所谓
"abcHELLOcba".removeprefix("abc")   # 'HELLOcba'   只从开头剥掉恰好一个 "abc"

"ababHELLO".strip("abc")        # 'HELLO'      a、b 反复剥到剥不动为止
"ababHELLO".removeprefix("ab")  # 'abHELLO'    只剥一次，剩下的 "ab" 不管

"cba_x".strip("abc")            # '_x'         "cba" 不是 "abc"，但字符都在集合里，照剥
"cba_x".removeprefix("abc")     # 'cba_x'      前缀对不上，原样返回，不报错

"http://a.com".strip("http://")     # 'a.com'  ← 看着对了
"tphttp://a.com".strip("http://")   # 'a.com'  ← 其实把开头的 tp 也吃了
"http://a.com".removeprefix("http://")  # 'a.com'   ← 这才是真的「去前缀」
```

最后两行是这个误用的典型形态：`strip` 恰好给出正确答案，是因为待剥的字符碰巧都在
`{h,t,p,:,/}` 里，换一份数据就会多剥。**要去掉的是「一个确定的子串」时，
永远用 `removeprefix` / `removesuffix`**；`strip` 只该用来清理**不定量的空白或填充字符**。

3.9 之前没有 `removeprefix`，等价写法是先判断再切片：

```python
if s.startswith(p):
    s = s[len(p):]              # ✅ 3.9 之前的标准写法
```

### 分割与拼接

| 方法 | 作用 |
| --- | --- |
| ★ `s.split()` | 按**任意空白**切分，**自动忽略连续空白和首尾空白** |
| ★ `s.split(sep[, maxsplit])` | 按 `sep` 切分，**连续 `sep` 会产生空串** |
| `s.rsplit(sep, k)` | 从右切，最多切 `k` 次 |
| `s.splitlines()` | 按行切分（认 `\n` `\r` `\r\n`） |
| `s.partition(sep)` | 切成三元组 `(前, sep, 后)`，只切第一次 |
| `s.rpartition(sep)` | 同上，从右切 |
| ★ `sep.join(iterable)` | 用 `sep` 连接可迭代对象里的**字符串** |

**`split()` 和 `split(' ')` 的差异是竞赛输入解析的高频坑**：

```python
"a b  c".split()            # ['a', 'b', 'c']          ← 连续空格合并
"a b  c".split(" ")         # ['a', 'b', '', 'c']      ← 多出一个空串！
"a,b,,c".split(",")         # ['a', 'b', '', 'c']
```

读输入永远用**无参数的 `split()`**，它同时处理空格、Tab、换行，且天然忽略首尾空白。

```python
"-".join(["a", "b", "c"])   # 'a-b-c'
"".join(map(str, [1, 2, 3]))    # '123'
"".join([1, 2])             # ❌ TypeError: 元素必须是 str，先 map(str, ...)
```

### 替换与映射

| 方法 | 作用 |
| --- | --- |
| ★ `s.replace(old, new[, cnt])` | 把 `old` 换成 `new`，可选的 `cnt` 限制最多换几次 |
| `str.maketrans(a, b[, del])` | 造字符映射表 |
| `s.translate(table)` | 按映射表批量替换单字符 |

```python
"abcabc".replace("a", "X")          # 'XbcXbc'
"abcabc".replace("a", "X", 1)       # 'Xbcabc'
"a b c".replace(" ", "")            # 'abc'   ← 删空格的标准写法

tab = str.maketrans("abc", "xyz")
"aabbcc".translate(tab)             # 'xxyyzz'
```

> **一次替换多种字符时用 `translate`，不要链式 `replace`**。
> `s.replace('a','x').replace('b','y').replace('c','z')` 要扫 3 遍串，
> `translate` 只扫 1 遍，且是 C 实现。凯撒密码、字符映射类题目直接用它。

### 复杂度速查

| 操作 | 复杂度 | 备注 |
| --- | --- | --- |
| `len(s)` | $O(1)$ | 长度是存好的 |
| `s[i]` | $O(1)$ | |
| `s[i:j]` | $O(j-i)$ | **复制** |
| `s + t` | $O(\|s\|+\|t\|)$ | 循环里用就是 $O(n^2)$ |
| `s * k` | $O(k\|s\|)$ | |
| `t in s`、`s.find(t)` | 最坏 $O(\|s\|\|t\|)$，实测接近线性 | CPython 用了 two-way 算法 |
| `s.count(t)` | 同上 | |
| `s.split()` | $O(\|s\|)$ | |
| `sep.join(a)` | $O(\sum \|a_i\|)$ | |
| `s[::-1]` | $O(\|s\|)$ | 比 `"".join(reversed(s))` 快 |
| `s.replace` / `translate` | $O(\|s\|)$ | |
| `s == t` | $O(\min(\|s\|,\|t\|))$ | 长度不等直接 `False`，$O(1)$ |
| `hash(s)` | $O(\|s\|)$ 首次，之后 $O(1)$ | 结果会缓存在字符串对象里 |
| `ord(c)` / `chr(i)` | $O(1)$ | |

---

## 5　三种格式化

Python 有三套字符串格式化语法，都还活着，都要认识。

> **格式化产生的是一个新字符串，跟 `print` 没有绑定关系。**
> `%` 是一个二元运算符（左边是格式串、右边是值），`f"..."` 是一个字符串字面量，
> `.format()` 是一个普通方法——三者都是**表达式**，求值结果是 `str`，
> 能赋值、能拼接、能当参数传、能当字典的键：
>
> ```python
> line = "%d" % x                 # 赋值：line 现在是一个 str
> tag = f"{x:.2f}"                # 同上
> out.append(f"{a} {b}")          # 收进列表，最后 "\n".join 一次输出
> print(f"{x:.6f}")               # print 只是恰好把这个 str 打出去而已
> ```
>
> 常见的困惑是「能不能对某个变量原地格式化」。**不能**——`str` 不可变，
> 格式化只会造出新串，想让变量指向它就得重新绑定：
>
> ```python
> x = 3.14159
> x = "%.2f" % x                  # 可以这么写，但 x 的类型从 float 变成了 str
> print(x + 1)                    # ❌ TypeError：它现在是字符串 '3.14'
> ```
>
> **算法题里几乎永远不该这么写**：数值就一直保持数值，只在**最终输出的那一刻**
> 才格式化成串。中途转成字符串，后面所有算术都得再转回来，还会白丢精度。

| 写法 | 语法 | 何时用 |
| --- | --- | --- |
| `%` 旧式 | `"%d" % x` | 只输出一个浮点数时最短 |
| `str.format` | `"{}".format(x)` | 需要重复使用同一参数时 |
| f-string | `f"{x}"` | **默认选择**，最快最短（3.6+） |

### 一、`%` 格式化

```python
"%d" % 42                       # '42'
"我叫 %s 今年 %d 岁" % ("小明", 10)     # 多个参数必须用元组
"%.3f" % 3.14159                # '3.142'
"%5.2f|%-5d|%+d" % (3.14159, 42, 7)     # ' 3.14|42   |+7'
"%o %x %X %e" % (64, 255, 255, 12345.7) # '100 ff FF 1.234570e+04'
"%%"                            # 输出一个百分号
```

| 占位符 | 含义 |
| --- | --- |
| `%d` `%i` | 整数 |
| `%s` | 任意对象（调用 `str()`） |
| `%f` | 浮点，默认 6 位小数 |
| `%e` `%E` | 科学计数法 |
| `%g` `%G` | 自动在 `%f` 和 `%e` 之间选 |
| `%o` `%x` `%X` | 八 / 十六进制 |
| `%c` | 按 ASCII 码或单字符 |

辅助指令：`%[标志][宽度][.精度]类型`，标志有 `-`（左对齐）、`+`（显示正号）、`0`（补零）、`#`（加 `0x`/`0o` 前缀）。

> `"%d" % x` 里 `x` 如果是元组会被当成多个参数，
> 想输出一个元组必须写 `"%s" % (t,)`。这是 `%` 格式化最容易踩的坑，也是 f-string 胜出的原因之一。

### 二、`str.format`

```python
"{} {}".format("a", "b")            # 'a b'          按顺序
"{0} {1} {0}".format("a", "b")      # 'a b a'        按下标，可重复
"{x} {y}".format(x=1, y=2)          # '1 2'          按名字
"{:>8}".format("hi")                # '      hi'     右对齐
"{:.3f}".format(1 / 3)              # '0.333'
"{:08.3f}".format(1 / 3)            # '0000.333'
```

### 三、f-string（推荐）

f-string 在**编译期**就展开成字符串拼接指令，运行时不需要解析格式串，
所以它是三者中**最快**的。花括号里可以放任意表达式：

```python
n, x = 255, 1 / 3
f"{n}"                  # '255'
f"{n + 1}"              # '256'         ← 里面可以写表达式
f"{x:.3f}"              # '0.333'
f"{n:08b}"              # '11111111'    ← 二进制补零到 8 位
f"{n:#x}"               # '0xff'
f"{n:,}"                # '255'         千位分隔符
f"{n:^9}"               # '   255   '   居中
f"{'YES' if n else 'NO'}"               # 三元也能塞
f"{x=}"                 # 'x=0.3333333333333333'   ← 3.8+，调试神器
```

格式说明符的完整形式：

```
{值:[[填充]对齐][符号][#][0][宽度][,][.精度][类型]}
```

| 部分 | 取值 | 含义 | 例子 |
| --- | --- | --- | --- |
| 填充 + 对齐 | `<` 左 `>` 右 `^` 中 `=` 符号后填充 | 不足宽度时补什么、往哪边靠 | `f"{s:*^10}"` |
| 符号 | `+` 总显示 `-` 只负数 ` ` 正数留空格 | 正数要不要带号 | `f"{n:+d}"` |
| `#` | 只能是 `#` 本身 | **进制前缀开关**：给 `b`/`o`/`x`/`X` 加上 `0b`/`0o`/`0x` | `f"{255:#x}"` → `'0xff'` |
| `0` | 只能是 `0` 本身 | **补零开关**：等价于把填充字符设成 `0`、对齐设成 `=` | `f"{7:05d}"` → `'00007'` |
| 宽度 | 整数 | 补完之后的总宽度 | `f"{n:5d}"` |
| `,` / `_` | 只能是 `,` 或 `_` 本身 | 分组分隔符：`d` 下每 3 位一组，`b`/`o`/`x` 下每 4 位一组（`,` 只支持 `d`） | `f"{1234567:,}"` → `'1,234,567'` |
| 精度 | `.k` | 小数位数（`f`/`e`）或最大字符数（`s`） | `f"{x:.6f}"` |
| 类型 | `d` `b` `o` `x` `X` `f` `e` `g` `%` `s` | 按哪种格式渲染 | `f"{n:b}"` |

`#` 和 `0` 这两位都是**开关**——写上就生效，不写就没有，它们没有取值：

```python
f"{255:x}"          # 'ff'        不带前缀
f"{255:#x}"         # '0xff'      井号打开前缀
f"{255:#b}"         # '0b11111111'
f"{7:5d}"           # '    7'     宽度 5，默认用空格补在左边
f"{7:05d}"          # '00007'     0 打开补零
f"{-7:05d}"         # '-0007'     补零认符号：零补在负号之后，总宽仍是 5
f"{-7:>5}"          # '   -7'     对比：普通右对齐把负号当普通字符一起靠右
f"{255:#07x}"       # '0x000ff'   两个开关一起用；宽度 7 是含前缀的总宽
```

`0` 与 `zfill` 的关系和 §4 说的一样：`f"{n:05d}"` 就是 `str(n).zfill(5)`，
都会把零补在符号后面。

竞赛里最常用的三个：

```python
f"{x:.6f}"          # 保留 6 位小数（spj 浮点题）
f"{n:09d}"          # 补前导零
f"{n:b}"            # 转二进制串，不带 0b 前缀
```

> f-string 内部**不能出现反斜杠**（3.12 之前）。
> 想在 f-string 里放换行要先定义 `NL = "\n"` 再写 `f"{NL}"`，或者干脆别这么写。

---

## 6　三引号与多行字符串

```python
para = """第一行
第二行
第三行"""
```

三引号保留其中的**所有**换行和空格，所见即所得。用途：

1. **多行注释**（本质是一个没被赋值的字符串表达式，见 [语法与执行模型](syntax.md#4-注释)）。
2. **docstring**——配套题解都用它写「这题考什么」。
3. 本地造测试数据：

```python
DATA = """3
1 2
3 4
5 6
"""
for line in DATA.strip().split("\n"):
    print(sum(map(int, line.split())))
```

> 三引号字符串的第一行如果紧跟引号换行，会**多出一个开头的 `\n`**：
> `"""\nabc"""` 的第一个字符是换行。要么用 `"""\` 续行，要么 `.strip()`。

---

## 7　字符与 ASCII：`ord` 与 `chr`

Python 没有 `char`，字符和整数之间的桥梁是这两个内置函数：

```python
ord("A")        # 65      字符 → 码点
chr(65)         # 'A'     码点 → 字符
ord("a")        # 97
ord("0")        # 48
```

竞赛里的标准用法——**把字母映射成 0..25 的下标**：

```python
idx = ord(c) - ord("a")         # 'a'→0, 'b'→1, ..., 'z'→25
idx = ord(c) - 97               # 同上，少一次函数调用，更快
c = chr(idx + 97)               # 反向

cnt = [0] * 26                  # 26 个字母的桶
for c in s:
    cnt[ord(c) - 97] += 1
```

记住这几个常数就不用查表了：

| 字符 | 码点 |
| --- | --- |
| `'0'` | 48 |
| `'A'` | 65 |
| `'a'` | 97 |
| `'a' - 'A'` | 32 |

因为大小写只差第 5 位（$32 = 2^5$），有个位运算小技巧：

```python
c = chr(ord(c) ^ 32)            # 大小写互换（仅对英文字母有效）
```

批量转换用 `map`：

```python
codes = list(map(ord, s))               # 字符串 → 码点列表
s = "".join(map(chr, codes))            # 码点列表 → 字符串
vals = [ord(c) - 97 for c in s]         # 字母 → 0..25
```

> **更快的写法：直接用 `bytes`。**
> `s.encode()` 得到 `bytes`，而 `bytes` 迭代出来的**就是整数**：
> ```python
> for b in s.encode():        # b 已经是 int，省掉 ord
>     cnt[b - 97] += 1
> ```
> 从 `sys.stdin.buffer` 读进来的本身就是 `bytes`，连 `encode` 都省了。见 [输入输出处理](../toolkit/io.md)。

字符串之间的大小比较就是**按码点逐位比较**（字典序）：

```python
"abc" < "abd"       # True
"Z" < "a"           # True    大写字母码点更小
"abc" < "abcd"      # True    前缀更短的更小
```

---

## 8　bytes 与编码

Python 3 里 `str` 是 **Unicode 码点序列**，`bytes` 是**字节序列**，两者不能混用：

```python
s = "你好"
b = s.encode("utf-8")           # str → bytes: b'\xe4\xbd\xa0\xe5\xa5\xbd'
s2 = b.decode("utf-8")          # bytes → str: '你好'

len(s)                          # 2   ← 2 个字符
len(b)                          # 6   ← 6 个字节（UTF-8 里一个汉字 3 字节）
```

| 类型 | 字面量 | 元素类型 | 可变？ |
| --- | --- | --- | --- |
| `str` | `"abc"` | 长度 1 的 `str` | 否 |
| `bytes` | `b"abc"` | `int`（0–255） | 否 |
| `bytearray` | `bytearray(b"abc")` | `int` | **是** |

```python
b = b"abc"
b[0]                # 97    ← 是整数，不是 b'a'！
b[0:1]              # b'a'  ← 切片才是 bytes
list(b)             # [97, 98, 99]

ba = bytearray(b"abc")
ba[0] = 120                     # 可以原地改
bytes(ba)                       # b'xbc'
```

竞赛里用到 `bytes` 的场景只有两个：

1. **`sys.stdin.buffer.read()` 返回 `bytes`**。`int(b"123")` 合法，
   但要当字符串输出必须先 `.decode()`：

   ```python
   data = sys.stdin.buffer.read().split()
   n = int(data[0])                # ✅ 数字不用解码
   s = data[1].decode()            # ✅ 字符串必须解码
   print(data[1])                  # ❌ 输出 b'abc'，带引号，直接 WA
   ```

2. **`bytearray` 当高速字节数组用**。它比 `list` 省内存（1 字节 vs 8 字节指针），
   且 `find`/`count`/`rfind` 都是 C 级别扫描，适合做超大的 0/1 标记数组：

   ```python
   vis = bytearray(n)              # n 个 0，比 [0] * n 省 8 倍内存
   vis[i] = 1
   ```

> Python 3 里**所有字符串都是 Unicode**，没有 Python 2 的 `u"..."` 前缀之说
> （虽然为了兼容仍然允许写 `u"abc"`）。
> `len(s)` 数的是**码点**，不是字节；这跟 C++ 的 `std::string::size()` 完全不同。
> 好在竞赛数据几乎全是 ASCII，两者等价。

---

## 9　例题

<!-- CHAPTER-EXAMPLE-TABLE -->

### PIO10 单组_字符串（入门）

> 给定长度 $n \le 10^5$ 的小写字符串 $s$，将其倒置输出。
> 题面见 [原题](https://www.nowcoder.com/practice/e3a57b2ff6de4aefb82af98925df544e)。

```python
input()                             # 读掉 n，Python 用不上
print(input().strip()[::-1])
```

三个语言点：

- `s[::-1]` 是**反转的唯一推荐写法**。它在 C 层做一次反向内存拷贝，
  比 `"".join(reversed(s))` 快 2–3 倍，比 `for` 循环快一个数量级。
- **`strip()` 不能省**，理由见 §1 的 `\r` 陷阱。
- `n` 这一行**必须读掉**，否则第二个 `input()` 拿到的还是 `n`。

### PIO11 多组_字符串_T组形式（入门）

> $t \le 10^5$ 组，每组给 $n$ 和串 $s$，$\sum n \le 10^5$。

数据量上来了，改用 token 流。因为串内保证无空格，**一个字符串就是一个 token**：

```python
import sys


def main():
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    out = []
    p = 1
    for _ in range(t):
        p += 1                      # 跳过 n
        out.append(data[p].decode()[::-1])
        p += 1
    sys.stdout.write("\n".join(out) + "\n")


main()
```

`data[p]` 是 `bytes`，`.decode()` 之后才是 `str`。
其实 `bytes` 也支持 `[::-1]`（反转字节），对纯 ASCII 结果一样，
但 `"\n".join(...)` 要求元素是 `str`，所以解码不能省。

> 也可以反过来：全程不解码，最后用 `b"\n".join(out)` 写进 `sys.stdout.buffer`。
> 这样更快，但可读性差，数据量到 $10^6$ 再考虑。

### PIO12 单组_二维字符数组（入门）

> $n \times m$ 的字符矩阵（$n, m \le 10^3$），**行和列都倒置**后输出。

「行列都倒置」拆成两步，两步都是切片：

- 每一行内部反转 → `row[::-1]`
- 行的顺序反转 → `reversed(rows)`

```python
import sys


def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    # 每行不含空格，所以一行就是一个 token；data[0]、data[1] 是 n 和 m，
    # 矩阵第 i 行因此落在 data[2 + i]，这个 2 就是跳过 n、m 的偏移量
    rows = [data[2 + i].decode() for i in range(n)]
    # r[::-1] 步长为 -1，从尾扫到头，即行内字符反转；
    # reversed(rows) 再把行的先后顺序翻过来，两者合起来就是「行列都倒置」
    sys.stdout.write("\n".join(r[::-1] for r in reversed(rows)) + "\n")


main()
```

`reversed()` 返回迭代器，不复制列表；配合生成器表达式喂给 `join`，全程不产生多余的中间列表。
注意 `m` 读进来也用不上——每行本身就是一个完整 token。

### PIO13 多组_带空格的字符串_T组形式（入门）

> $t$ 组，每组给一个**含空格**的串，去掉空格后倒置输出。保证首尾不是空格。

**这题是 token 流的反例**。`split()` 会把 `"one space"` 切成两个 token，
行边界信息丢失后无法还原，必须按行读：

```python
import sys


def main():
    inp = sys.stdin
    t = int(inp.readline())
    out = []
    for _ in range(t):
        inp.readline()                          # 跳过 n
        s = inp.readline().rstrip("\n")
        out.append(s.replace(" ", "")[::-1])
    sys.stdout.write("\n".join(out) + "\n")


main()
```

- **删空格用 `s.replace(" ", "")`**，$O(n)$ 一遍扫描。
  不要用 `"".join(s.split())`——那会把连续空格合并成一个再删，结果虽然一样但绕了一圈。
- `rstrip("\n")` 只去换行，**不能用 `strip()`**：题目保证首尾无空格，
  但一旦哪天不保证，`strip()` 会连有意义的空格一起吃掉。
- 用 `sys.stdin.readline` 而不是 `input()`，快 5–10 倍。

> **判断口诀**：串内可能含空格 → 按行读；确定无空格 → token 流。
> 完整讨论见 [输入输出处理](../toolkit/io.md#5-字符串的读入)。

### BISHI10 小红的字符串修改（简单，字符串 / 模拟）

> 给定小写串 $s$ 与 $t$（$|s| \le |t| \le 10^3$）。每次操作可把某个字母换成**字母表中相邻**的字母
> （`a` 可换成 `b` 或 `z`，即字母表首尾相连）。求最少操作次数，使 $s$ 成为 $t$ 的子串
> （这里的「子串」= 连续子串）。
> 题面见 [原题](https://www.nowcoder.com/practice/66e0054ff6b345afa47bcd4e8ceb72d7)。

**拆成两层。**

第一层，单个字符的代价。把 `a`–`z` 编号 $0$–$25$，字母表首尾相连构成一个环，
从 $a$ 走到 $b$ 的最少步数就是环上距离：

$$\text{cost}(a, b) = \min(|a-b|,\ 26 - |a-b|)$$

第二层，`s` 长度固定，所以它只能对齐到 `t` 的某个起点 $i \in [0, m-n]$，
枚举起点、逐位累加即可：

$$\text{ans} = \min_{0 \le i \le m-n} \sum_{j=0}^{n-1} \text{cost}(s_j,\ t_{i+j})$$

```python
import sys


def main():
    data = sys.stdin.buffer.read().split()
    s = data[0].decode()
    t = data[1].decode()
    n, m = len(s), len(t)

    # 预处理 26x26 代价表：字母表是环形的，a 和 z 相邻
    cost = [[min(abs(a - b), 26 - abs(a - b)) for b in range(26)]
            for a in range(26)]

    # 转成 0..25 的下标数组，循环里就不用反复调 ord
    sa = [ord(c) - 97 for c in s]
    ta = [ord(c) - 97 for c in t]

    print(min(
        sum(cost[sa[j]][ta[i + j]] for j in range(n))
        for i in range(m - n + 1)
    ))


main()
```

**复杂度**：$O(n(m-n+1))$。乍看是 $O(nm) = 10^6$，但 $n(m-n+1)$ 在 $n = m/2$ 时取到最大值
$\approx m^2/4 = 2.5 \times 10^5$，实测 0.06 秒，完全不用担心。

四个本章知识点在这里全用上了：

| 用到的点 | 位置 |
| --- | --- |
| `ord(c) - 97` 把字母映射成下标 | `sa`、`ta` |
| 字符串按下标随机访问是 $O(1)$ | `ta[i + j]` |
| 预处理代价表避免循环内重复计算 | `cost` |
| 生成器表达式喂给 `min`/`sum`，全程不建中间列表 | 最后三行 |

> **常见错误**：忘了字母表是**环形**的，直接写 `abs(a - b)`。
> 示例 2 里 `z` → `a` 只要 1 步而不是 25 步，正是用来卡这个的。

---

## 10　本章速查

| 场景 | 写法 |
| --- | --- |
| 反转字符串 | `s[::-1]` |
| 判回文 | `s == s[::-1]` |
| 去首尾空白 / 去 `\r` | `s.strip()` |
| **循环拼接字符串** | **禁止 `+=`，用 `"".join(parts)`** |
| 需要按下标改字符 | `a = list(s)` → 改 → `"".join(a)` |
| 切分输入 | 永远用无参 `s.split()` |
| 删除某字符 | `s.replace(" ", "")` |
| 批量字符映射 | `s.translate(str.maketrans(a, b))` |
| 字母 → 0..25 | `ord(c) - 97` |
| 0..25 → 字母 | `chr(i + 97)` |
| 26 字母计数 | `cnt = [0]*26; cnt[ord(c)-97] += 1` |
| 保留 $k$ 位小数 | `f"{x:.6f}"`（严格四舍五入见[浮点与科学计数法](../toolkit/float.md)） |
| 补前导零 | `s.zfill(k)` 或 `f"{n:09d}"` |
| 数转二进制串 | `f"{n:b}"`，不带 `0b` 前缀 |
| 判合法整数 | `try: int(s)`，**不要用 `isdigit()`** |
| `bytes` 转 `str` | `.decode()`；数字可以直接 `int(b"123")` |
| 大量输出 | `sys.stdout.write("\n".join(out) + "\n")` |
| 子串查找 | `s.find(t)` 返回 `-1`；`s.index(t)` 抛异常 |
| 重叠计数 | `s.count(t)` **不重叠**，需重叠请用 KMP |
| 去前缀 | `s.removeprefix(p)`（3.9+），**不是** `strip(p)` |

"""BISHI21 【模板】排序 —— 把 n 个整数按非递减顺序排好并输出成一行。

这题考什么：
    算法层面就一句话：调用内置排序。但它作为模板题的真正意义在于让读者
    看清「n = 1e5 时时间花在哪里」——排序本身是 O(n log n) 的 C 实现，
    在这个量级上只要几十毫秒；真正会把程序拖垮的是逐行读入和逐个输出。

    所以标准写法固定成三步，后面几乎每道题都会重复它：
      1. sys.stdin.buffer.read().split() 一次性把输入切成 token 列表；
      2. 中间处理（这里是 sorted(map(int, ...))，Timsort，O(n log n)）；
      3. " ".join(map(str, a)) 拼成一整行，一次 sys.stdout.write 输出。
    对比 1e5 次 input() 加 1e5 次 print，这套写法通常能快一个数量级。
    完整的性能对照见 docs/part2-竞赛基本功/21-复杂度与Python性能.md，
    排序本身的更多用法见 docs/part4-基础算法/40-排序.md。

数据规模与复杂度：
    n <= 1e5，|a_i| <= 1e9。
    排序 O(n log n) 约 1.7e6 次比较，全部发生在 C 层；
    map(int, ...) 的 1e5 次转换和 join 的 1e5 次格式化同样是 C 层循环。
    整体在「其他语言 2 秒」的限制下余量很大。

坑在哪：
  1. **不要直接对 bytes 排序**。data 里的 token 是 bytes，排序会按字典序比较：
     b"10" 会排在 b"9" 前面，负号 b"-" 的 ASCII 码又比数字小，
     负数会全部挤到最前面且内部顺序还是反的。必须先 map(int, ...) 转成整数；
  2. 只取前 n 个 token（data[1:n + 1]），不要用 data[1:]。
     输入末尾若有多余的空白或脏数据，切到底会把它们一起排进去；
  3. 输出是**一行**、以空格分隔，不是每个数一行；
  4. a_i 可以是负数（-1e9 <= a_i <= 1e9），任何「按无符号处理」的取巧写法都会错。

样例复核：
    n = 5、数组 5 4 3 2 1，排序后 1 2 3 4 5，输出 "1 2 3 4 5"，与样例一致。
"""
import sys

data = sys.stdin.buffer.read().split()
n = int(data[0])
# 只取前 n 个 token，转成 int 再排序（对 bytes 排序得到的是字典序，负数会全错）
a = sorted(map(int, data[1:n + 1]))
sys.stdout.write(" ".join(map(str, a)) + "\n")

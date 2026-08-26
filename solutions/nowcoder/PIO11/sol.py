"""PIO11 多组_字符串_T组形式 —— t 组，每组给长度 n 和一个小写字母串，各自倒置输出。

这题考什么：
    输入形态：T 组形式，数据本体是不含空格的字符串。

    串内只有小写英文字母、没有空格，这一条是本题能按 token 读的全部依据：
    split() 按空白切分，而串里没有空白，所以每个串恰好是一个完整 token，
    token 边界与字符串边界重合。一旦串内可能含空格，这套写法立刻失效，
    必须改成按行读（见 PIO13）。

    游标 p 从 1 起步（跳过首个 token t），每组先 p += 1 跳过该组的 n，
    取走字符串，再 p += 1 指向下一组的 n。

为什么必须一次性读入：
    t 最大 1e5，每组两行，总行数可达 2e5 + 1；而 sum(n) 只有 1e5，
    数据本体很小、组数很多，成本几乎全在每组的固定调用开销上。
    逐行 input() 要付出二十万次调用，buffer.read() 只有一次。
    输出同理：t 行结果攒进 out，最后 join 成一整块 write，只有一次输出调用。

为什么这里要 .decode()：
    buffer.read().split() 得到的 token 是 bytes（字节串）而不是 str（文本串）。
    数字场景下 int() 能直接解析 bytes，所以前面几题都不用管；
    但这一题 token 本身就是答案的一部分，必须转成 str 才能参与文本拼接。

数据规模与复杂度：
    t <= 1e5，sum(n) <= 1e5。时间 O(t + sum(n))，空间 O(token 总数)。
    倒置用切片 s[::-1]，C 层完成，O(n)。

坑在哪：
  1. bytes 当 str 用是这一题最典型的错误。忘记 decode 时，
     bytes 也支持 [::-1]，代码照样跑，但 join 一个 bytes 列表会抛 TypeError；
     若改用 print 直接输出，屏幕上会出现 b'edcba' 这样带前缀和引号的形式。
     同样，data[p] == "abc" 这种比较恒为 False，因为 bytes 与 str 永不相等。
  2. 每组消费两个 token（n 和串），两次 p += 1 缺一不可，
     漏掉跳过 n 的那次会把长度数字当成待倒置的串。
  3. p 的初值是 1 不是 0，下标 0 已被 t 占用。
"""
import sys

data = sys.stdin.buffer.read().split()
t = int(data[0])
out = []
p = 1                                     # 下标 0 是组数 t，数据从 1 开始
for _ in range(t):
    p += 1                                # 跳过 n
    # token 是 bytes，必须 decode 成 str 才能参与后面的文本拼接
    out.append(data[p].decode()[::-1])
    p += 1                                # 跳过刚取走的字符串，指向下一组的 n
sys.stdout.write("\n".join(out) + "\n")

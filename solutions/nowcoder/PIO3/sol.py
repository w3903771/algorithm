"""PIO3 多组_A+B_EOF形式 —— 不给组数，一直读到文件末尾。

这题考什么：
    输入形态：多组数据，以 EOF（end of file，文件末尾）结束。
    题目不告诉你有几组，程序必须自己判断「没有更多数据了」。

    Python 里判断 EOF 最自然的写法是 for line in sys.stdin：
    文件对象本身就是可迭代对象，迭代到数据耗尽时循环自然结束，
    既不需要哨兵，也不需要异常。

为什么不用 while True + try/except EOFError：
    那种写法有两个问题。其一，它每轮都调用 input()，而 input() 的开销按调用
    次数累积，行数上万时会明显拖慢（见 docs/toolkit/io.md
    的读入方式对比表）。其二，它把「正常结束」写成了异常路径——
    循环的终止条件藏在 except 里，读代码的人得跳着看才知道循环什么时候停。
    for line in sys.stdin 把终止条件放回了循环头部，这是它更好的主要原因。

为什么这一题按行读而不是一次 read().split()：
    两种都能过。按行读能让「一行一组数据」的结构直接体现在代码里，
    与 EOF 形态的语义最贴合；代价是要自己处理空行。
    如果只追求速度，可以像 PIO4 那样把全部 token 一次读进来——
    对 EOF 形态尤其省事，因为 token 流本来就不关心有几组。

数据规模与复杂度：
    a, b 不超过 1e9，组数由数据决定。时间 O(总行数)，空间 O(总行数)
    （out 列表存下全部答案）。

坑在哪：
  1. 文件末尾常常多出一个空行或只含空白的行。不跳过它，
     map(int, line.split()) 会解包失败，直接运行时错误。
     判断写成 if not line.split() 而不是 if not line.strip()，
     是因为后面本来就要 split 一次，语义统一。
  2. 输出必须先攒进 out，最后 join 成一整块一次性写出。
     组数未知且可能上万，逐行 print 要走上万次 Python 层的输出流程，
     一次 write 只走一次。
  3. 末尾要补一个行尾换行，否则最后一行没有换行符，部分判定环境会报格式错误。
"""
import sys

# out 先攒着，全部算完再一次性写出，避免上万次 print 的调用开销
out = []
for line in sys.stdin:                    # 文件对象即迭代器，读到 EOF 自然停止
    if not line.split():                  # 跳过空行与纯空白行，否则下面解包会失败
        continue
    a, b = map(int, line.split())
    out.append(a + b)
sys.stdout.write("\n".join(map(str, out)) + "\n")

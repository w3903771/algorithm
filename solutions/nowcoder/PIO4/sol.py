"""PIO4 多组_A+B_T组形式 —— 首行给出组数 t，随后 t 行每行两个整数。

这题考什么：
    输入形态：多组数据，T 组形式（首行是组数）。这是竞赛里最常见的形态。
    组数已知，所以程序不必判断 EOF，按计数循环即可。

    读入用的是竞赛里最通用的高速范式：一次性把整个标准输入读成字节串，
    按空白切成 token 列表，然后用下标定位每一个数。
    sys.stdin.buffer.read() 绕开了文本层的解码和换行处理，
    .split() 在 C 层一次切完，整个过程只有一次系统调用。

    切完之后 token 流里已经没有「行」的概念了，
    第 i 组（i 从 0 数起）的两个数固定落在下标 1 + 2i 和 2 + 2i：
    下标 0 被 t 占掉，所以每组的起点都要加 1 这个偏移量。

为什么不逐行 input()：
    t 最大 1e5，意味着最多 1e5 次 input() 调用。input() 每次都要走
    提示符逻辑、编码解码、去换行三层处理，开销按调用次数累积；
    而 buffer.read() 无论多少行都只读一次。两者在 1e5 行量级上差一个数量级，
    这正是 Python 选手「写对了却超时」的最常见原因。

    输出同理：t 行答案若逐行 print，就是 1e5 次输出调用；
    先攒进 out，最后 join 成一整块 write 出去，只有一次。

数据规模与复杂度：
    t <= 1e5，a, b <= 1e9，token 总数约 2e5 + 1。
    时间 O(t)，空间 O(t)。和最大 2e9，超过 32 位整数上限，
    但 Python 的 int 任意精度，不会溢出。

坑在哪：
  1. data 里的元素是 bytes 而不是 str。int(b"123") 是合法的
     （Python 会按 ASCII 解析），所以数字不需要 decode；
     但如果直接把 data[0] 打印出来，屏幕上会看到 b'3' 这样带前缀的形式，
     拿它和字符串比较（data[0] == "3"）也恒为 False。
     只有当 token 本身要当字符串用时才需要 .decode()（见 PIO11）。
  2. 下标里的 +1 偏移不能漏。写成 data[2 * i] 会把 t 当成第一组的 a，
     全部答案错位。
  3. 组数以首行的 t 为准，不要用 len(data) 反推。
"""
import sys

# 一次性读入全部 token；元素是 bytes，int() 可直接解析，无需 decode
data = sys.stdin.buffer.read().split()
t = int(data[0])                          # 下标 0 是组数，后面每组的起点都要跳过它
out = []
for i in range(t):
    a = int(data[1 + 2 * i])              # 第 i 组的两个数：偏移 1 是为了跳过 t
    b = int(data[2 + 2 * i])
    out.append(a + b)
sys.stdout.write("\n".join(map(str, out)) + "\n")

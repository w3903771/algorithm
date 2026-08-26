# 来源: 牛客 · 面试必刷TOP101　简单
# 链接: https://www.nowcoder.com/practice/54275ddae22f475981afa2244dd448c6
# 判题: 核心代码模式
# 签名: 需实现 push、pop，判题走 driver.py

"""BM42 用两个栈实现队列 —— 一个栈只管进、一个栈只管出，倒一次序就把「后进先出」翻成「先进先出」。

这题考什么：
    栈是后进先出、队列是先进先出，两者差的正好是「一次逆序」。
    把元素从一个栈整体倒进另一个栈，出栈顺序就恰好反过来，于是两个栈分工：

      - stack_in  只接收 push，新元素永远压在它上面；
      - stack_out 只负责 pop，栈顶就是当前最老的元素。

    pop 时如果 stack_out 是空的，就把 stack_in 里的元素**整体**倒过去，
    倒完之后 stack_out 的栈顶就是队首；stack_out 非空时**绝不能倒**，
    否则新元素会插到老元素前面，先进先出就被破坏了。

    每个元素一生只经历「进 in、出 in、进 out、出 out」四次操作，
    所以虽然单次 pop 可能倒一大批，n 次操作的总代价仍是 O(n)——
    这就是「均摊 O(1)」：单次不保证快，一整段操作平均下来才是常数。

数据规模与复杂度：
    n <= 1000，push 与 pop 各 n 次，时限「其他语言 2 秒」。
    时间 push O(1)、pop 均摊 O(1)，全程 O(n)；空间 O(n)，两个栈加起来最多装 n 个元素。
    反面写法是每次 pop 都把 out 倒回 in、再整体倒过来，单次 O(n)、总计 O(n^2) = 1e6，
    本题规模下仍能过，但它不满足题面要求的「插入与删除时间复杂度都是 O(1)」。

坑在哪：
  1. 牛客把参数编进了操作名里：输入形如 ["PSH1","PSH2","POP","POP"]，
     PSH<n> 就是 push(n)、POP 就是 pop()，期望输出是各次 pop 的返回值按逗号拼接。
     函数签名里看不出这套约定，判题因此交给 driver.py 驱动。
     把 PSH1 当成不带参数的操作名、或以为 push 会一次收到整个数组，都会跑偏。
  2. stack_out 非空时搬运会直接出错：新元素倒过去会压在老元素上面，
     下一次 pop 弹出的是后进的元素，队列退化成栈。搬运的前提就是「out 已经空了」。
  3. 题目保证 pop 时队列内已有元素，所以 stack_out.pop() 不再判空；
     若去掉这个保证，两栈皆空时会抛 IndexError，需要另行约定返回值。

样例复核：
    ["PSH1","PSH2","POP","POP"]：push 1、push 2 后 in = [1, 2]、out 为空；
    第一次 pop 把 in 倒空得到 out = [2, 1]，弹出栈顶 1；
    第二次 pop 时 out 非空，直接弹出 2。输出 1,2，与样例一致。
"""
from typing import List, Optional


class Solution:
    def __init__(self) -> None:
        # 两个栈分工固定：in 端只进、out 端只出，元素从 in 倒进 out 时完成唯一一次逆序
        self.stack_in: List[int] = []    # 只接收入队元素
        self.stack_out: List[int] = []   # 只吐出出队元素，栈顶即队首

    def push(self, node: int) -> None:
        # 入队恒为 O(1)：只压 in，不去碰 out 里已经理好顺序的那批老元素
        self.stack_in.append(node)

    def pop(self) -> int:
        # 只有 out 空了才搬运；out 非空时搬运会把新元素压到老元素上面，先进先出即失效
        if not self.stack_out:
            # 一次倒空：每个元素一生只被搬运一次，n 次操作的搬运总数不超过 2n，故均摊 O(1)
            while self.stack_in:
                self.stack_out.append(self.stack_in.pop())
        # 题目保证 pop 时队列内已有元素，因此这里不再判空
        return self.stack_out.pop()

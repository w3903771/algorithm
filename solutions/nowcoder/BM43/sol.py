# 来源: 牛客 · 面试必刷TOP101　简单
# 链接: https://www.nowcoder.com/practice/4c776177d2c04c2494f2555c9fcc1e49
# 判题: 核心代码模式
# 签名: 需实现 push、pop、top、min，判题走 driver.py

"""BM43 包含min函数的栈 —— 再开一个「最小值栈」与数据栈同步升降，栈顶永远是当前最小值。

这题考什么：
    难点在于 min 要 O(1)：每次现扫一遍是 O(n)，而 pop 之后最小值可能变大，
    只存一个 min 变量又救不回来——被弹掉的那个最小值一走，
    旧的最小值是多少就没人记得了。

    解法是给每个「栈的历史状态」都记一份最小值：
    额外维护一个与数据栈**等高**的 min_stack，min_stack[i] 表示
    「数据栈只有前 i+1 个元素时的最小值」。

      - push(v)：数据栈压 v，min_stack 压 min(v, 当前栈内最小)；
      - pop()  ：两个栈同时弹，历史最小值自动回退到上一层；
      - min()  ：直接读 min_stack[-1]。

    关键是两个栈永远同进同退，min_stack 才能和数据栈的每个历史状态一一对应。
    这是「用空间换掉一次扫描」的典型：多存 n 个数，换来 min 从 O(n) 降到 O(1)。

数据规模与复杂度：
    操作数量 0 <= n <= 300，元素满足 |val| <= 10000，时限「其他语言 2 秒」。
    四个方法都是 O(1)，空间 O(n)，正好对上题面进阶要求。
    规模其实很小——min 每次现扫也不过 300 * 300 = 9e4 次比较，照样能过，
    但那不是这题要考的东西：考点是「让每个历史状态自带答案」这个设计。

坑在哪：
  1. 调用约定与 BM42 同类：输入是把参数编进操作名的字符串数组
     ["PSH-1","PSH2","MIN","TOP","POP","PSH1","TOP","MIN"]，
     PSH<n> 是 push(n)，POP / TOP / MIN 分别对应另外三个方法；
     只有 TOP 与 MIN 有返回值，期望输出是这些返回值按逗号拼接（该例为 -1,2,1,-1）。
     判题走 driver.py。PSH-1 里的负号是参数的一部分，
     按「取第 4 个字符」解析就会把负数读错。
  2. pop 必须两个栈同步弹。只弹数据栈会让 min_stack 越长越高，
     min() 读到的是早已出栈的元素留下的最小值，从此再也对不上。
  3. 压缩版写法（只在「新值 <= 当前最小」时压 min_stack、pop 时相等才弹）
     必须用 <= 而不是 <：push 1、push 1、pop 之后栈里还有一个 1，
     而 < 只记了一次，pop 时把它弹掉，min 就会漏掉仍在栈中的那个 1。

样例复核：
    依次 push -1、push 2 后，数据栈 [-1, 2]、min_stack [-1, -1]：
    MIN 读 -1、TOP 读 2；POP 后两栈同退回到 [-1] 与 [-1]；
    再 push 1 得数据栈 [-1, 1]、min_stack [-1, -1]，TOP 读 1、MIN 读 -1。
    输出 -1,2,1,-1，与题面示例一致。
"""
from typing import List, Optional


class Solution:
    def __init__(self) -> None:
        # 两个栈等高，min_stack[i] 是「数据栈只有前 i+1 个元素时」的最小值
        self.stack: List[int] = []       # 数据栈
        self.min_stack: List[int] = []   # 与数据栈等高，记录各历史状态下的最小值

    def push(self, node: int) -> None:
        # 入栈：数据栈与最小值栈同步长高一层，历史状态才能一一对应
        self.stack.append(node)
        # 空栈时最小值就是它自己，否则与之前的最小值取小
        self.min_stack.append(node if not self.min_stack
                              else min(node, self.min_stack[-1]))

    def pop(self) -> None:
        # 两个栈必须同时弹：只弹数据栈，最小值就会停留在已经出栈的元素上
        self.stack.pop()
        self.min_stack.pop()             # 必须同步弹出，最小值才会正确回退

    def top(self) -> int:
        return self.stack[-1]

    def min(self) -> int:
        # 栈顶那一层记的就是「当前全栈最小值」，所以 min 与 top 一样只是一次读取
        return self.min_stack[-1]
